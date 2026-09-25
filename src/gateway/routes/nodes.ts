/**
 * gateway/routes/nodes.ts
 *
 * Node management APIs (admin):
 *   GET    /nodes           — list all nodes
 *   GET    /nodes/:id       — get a specific node
 *   POST   /nodes/:id/drain — initiate graceful drain
 *   DELETE /nodes/:id       — force remove (admin only)
 *
 * Internal APIs (used by storage nodes):
 *   POST   /internal/nodes/register   — node registration on startup
 *   POST   /internal/nodes/heartbeat  — periodic heartbeat
 *   POST   /internal/corruption       — report corruption from scanner
 */

import { Router, Request, Response } from 'express';
import type { MetadataService } from '../../metadata/service.js';
import type { Rebalancer } from '../../rebalancer/rebalancer.js';
import type { RepairWorker } from '../../repair/worker.js';

export function nodesRouter(
  metadata: MetadataService,
  rebalancer: Rebalancer,
  repairWorker: RepairWorker
): Router {
  const router = Router();

  // ─── Public: Node Listing ──────────────────────────────────────────────────

  router.get('/nodes', (_req: Request, res: Response) => {
    const nodes = metadata.getAllNodes();
    res.json({ nodes, count: nodes.length });
  });

  router.get('/nodes/:id', (req: Request, res: Response) => {
    const node = metadata.getNode(req.params.id);
    if (!node) {
      res.status(404).json({ error: 'Node not found' });
      return;
    }

    // Include replica count on this node
    const replicas = metadata.getReplicasOnNode(req.params.id);
    res.json({ ...node, replica_count: replicas.length });
  });

  // ─── Admin: Drain a node ──────────────────────────────────────────────────

  /**
   * POST /nodes/:id/drain
   *
   * Gracefully remove a node:
   *   1. Mark DRAINING (no new writes)
   *   2. Create repair jobs for all replicas on this node
   *   3. The repair worker migrates them in background
   */
  router.post('/nodes/:id/drain', async (req: Request, res: Response) => {
    const node = metadata.getNode(req.params.id);
    if (!node) {
      res.status(404).json({ error: 'Node not found' });
      return;
    }

    if (node.state === 'FAILED') {
      res.status(400).json({ error: 'Cannot drain a FAILED node' });
      return;
    }

    if (node.state === 'DRAINING') {
      res.status(400).json({ error: 'Node is already draining' });
      return;
    }

    // Check that there are enough other nodes to maintain quorum
    const healthyNodes = metadata.getHealthyNodes().filter(n => n.node_id !== node.node_id);
    if (healthyNodes.length < 2) { // Need at least W=2 other nodes
      res.status(400).json({
        error: 'Cannot drain: insufficient healthy nodes to maintain quorum',
        healthy_count: healthyNodes.length,
      });
      return;
    }

    const result = await rebalancer.drainNode(req.params.id);

    res.json({
      node_id: req.params.id,
      state: 'DRAINING',
      jobs_created: result.jobsCreated,
      message: `Node ${req.params.id} is draining. ${result.jobsCreated} replicas are being migrated.`,
    });
  });

  // ─── Internal: Node Registration (storage node → gateway) ─────────────────

  router.post('/internal/nodes/register', (req: Request, res: Response) => {
    const { node_id, address, port, storage_used, storage_total } = req.body as {
      node_id: string;
      address: string;
      port: number;
      storage_used: number;
      storage_total: number;
    };

    if (!node_id || !address || !port) {
      res.status(400).json({ error: 'node_id, address, and port are required' });
      return;
    }

    const node = metadata.registerNode({ node_id, address, port, storage_used, storage_total });

    // Trigger rebalancing if this is a genuinely new node
    const existingReplicas = metadata.getReplicasOnNode(node_id);
    if (existingReplicas.length === 0) {
      // New node with no replicas — schedule migrations
      setTimeout(() => rebalancer.onNodeJoined(node_id), 5000);
    }

    res.json({ node, message: 'Registered successfully' });
  });

  // ─── Internal: Heartbeat (storage node → gateway) ─────────────────────────

  router.post('/internal/nodes/heartbeat', (req: Request, res: Response) => {
    const { node_id, storage_used, storage_total } = req.body as {
      node_id: string;
      storage_used: number;
      storage_total: number;
    };

    if (!node_id) {
      res.status(400).json({ error: 'node_id is required' });
      return;
    }

    const node = metadata.getNode(node_id);
    if (!node) {
      res.status(404).json({ error: 'Node not registered' });
      return;
    }

    metadata.updateHeartbeat(node_id, storage_used ?? 0, storage_total ?? 0);
    res.json({ ok: true });
  });

  // ─── Internal: Corruption Report (storage node scanner → gateway) ──────────

  /**
   * POST /internal/corruption
   *
   * A storage node's integrity scanner detected a checksum mismatch.
   * The gateway marks the replica CORRUPT and schedules repair.
   */
  router.post('/internal/corruption', (req: Request, res: Response) => {
    const { node_id, object_id, expected_checksum, actual_checksum } = req.body as {
      node_id: string;
      object_id: string;
      expected_checksum: string;
      actual_checksum: string;
    };

    console.warn(
      `[Gateway] Corruption reported on node ${node_id}, object ${object_id} — ` +
      `expected: ${expected_checksum}, actual: ${actual_checksum}`
    );

    // Find the replica
    const replicas = metadata.getReplicasForObject(object_id);
    const corruptReplica = replicas.find(r => r.node_id === node_id);

    if (corruptReplica) {
      metadata.updateReplicaState(corruptReplica.replica_id, 'CORRUPT');
    }

    metadata.appendEvent(
      'CORRUPT_DETECTED',
      `Corrupt replica detected on node ${node_id} for object ${object_id}`,
      { node_id, object_id, expected_checksum, actual_checksum }
    );

    // Schedule repair
    if (corruptReplica) {
      repairWorker.scheduleRepairForCorruptReplica(object_id, node_id, corruptReplica.replica_id);
    }

    res.json({ received: true });
  });

  return router;
}
