/**
 * gateway/routes/objects.ts
 *
 * Client-facing object storage API:
 *   PUT    /objects/:key   — store an object
 *   GET    /objects/:key   — retrieve an object
 *   DELETE /objects/:key   — delete an object
 *   GET    /objects/:key/metadata — get metadata without downloading data
 */

import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import type { MetadataService } from '../../metadata/service.js';
import { Coordinator } from '../coordinator.js';
import { PlacementService } from '../placement.js';
import { computeChecksum } from '../../storage/checksum.js';
import type { VaultConfig } from '../../common/config.js';

export function objectsRouter(
  metadata: MetadataService,
  coordinator: Coordinator,
  placement: PlacementService,
  config: VaultConfig
): Router {
  const router = Router();

  // ─── PUT /objects/:key ─────────────────────────────────────────────────────

  /**
   * Store or update an object.
   *
   * The key is the user-facing identifier (e.g. "reports/q1.pdf").
   * The system assigns the object_id, version, and checksum.
   *
   * Write flow:
   *   1. Compute checksum of incoming bytes
   *   2. Look up existing object by key (versioning)
   *   3. Create/update object metadata (state: PENDING)
   *   4. Select N healthy nodes via PlacementService
   *   5. Write to all N nodes in parallel via Coordinator (quorum W)
   *   6. If quorum achieved → commit metadata (state: DURABLE)
   *   7. If quorum failed → rollback (object stays PENDING or is rolled back)
   *
   * Concurrent writes:
   *   If two clients PUT the same key simultaneously, the one that commits
   *   its metadata transaction last wins. The other's replicas become STALE
   *   and will be cleaned up by the repair worker.
   *
   * Optional header: X-Expected-Version: <n>
   *   If provided, the PUT is conditional — it only proceeds if the current
   *   version matches. Returns 409 if not.
   */
  router.put('/:key(*)', async (req: Request, res: Response) => {
    const key = req.params.key;
    const body = req.body as Buffer;

    if (!Buffer.isBuffer(body) || body.length === 0) {
      res.status(400).json({ error: 'Request body must be non-empty binary data' });
      return;
    }

    // Compute checksum before doing anything else
    const checksum = computeChecksum(body);

    // Check for conditional write (optimistic concurrency control)
    const expectedVersionHeader = req.headers['x-expected-version'];
    const expectedVersion = expectedVersionHeader
      ? parseInt(String(expectedVersionHeader), 10)
      : null;

    const existing = metadata.getObjectByKey(key);

    if (expectedVersion !== null) {
      const currentVersion = existing?.version ?? 0;
      if (currentVersion !== expectedVersion) {
        res.status(409).json({
          error: 'Version conflict',
          expected: expectedVersion,
          actual: currentVersion,
          message: 'Use X-Expected-Version: 0 for a new object, or the current version for an update',
        });
        return;
      }
    }

    // Create or update object in metadata (state: PENDING)
    let obj = existing
      ? metadata.updateObject(existing.object_id, { size: body.length, checksum })
      : metadata.createObject({
          logicalKey: key,
          size: body.length,
          checksum,
          replicationFactor: config.replicationFactor,
        });

    // Select target nodes
    const healthyNodes = metadata.getHealthyNodes();
    const targetNodes = placement.selectNodes(healthyNodes, config.replicationFactor);

    if (targetNodes.length === 0) {
      res.status(503).json({ error: 'No healthy storage nodes available' });
      return;
    }

    // Write to nodes with quorum
    const writeResult = await coordinator.writeQuorum(
      obj.object_id,
      obj.version,
      checksum,
      body,
      targetNodes,
      config.writeQuorum
    );

    if (!writeResult.success) {
      res.status(503).json({
        error: 'Write quorum not achieved',
        ack_count: writeResult.ackCount,
        required: config.writeQuorum,
        failed_nodes: writeResult.failures,
      });
      return;
    }

    // Quorum achieved — commit replicas and object state
    for (const node of targetNodes.filter(n => !writeResult.failures.includes(n.node_id))) {
      metadata.addReplica({
        objectId: obj.object_id,
        nodeId: node.node_id,
        version: obj.version,
        checksum,
        size: body.length,
      });
    }

    metadata.commitObject(obj.object_id);
    obj = metadata.getObjectById(obj.object_id)!;

    const replicas = metadata.getReplicasForObject(obj.object_id);

    metadata.appendEvent('OBJECT_WRITTEN', `Object "${key}" written (v${obj.version}, ${body.length} bytes)`, {
      object_id: obj.object_id,
      key,
      version: obj.version,
      size: body.length,
    });

    res.status(existing ? 200 : 201).json({
      object_id: obj.object_id,
      key,
      version: obj.version,
      size: obj.size,
      checksum: obj.checksum,
      state: obj.state,
      replicas: replicas.map(r => ({
        replica_id: r.replica_id,
        node_id: r.node_id,
        state: r.state,
      })),
    });
  });

  // ─── GET /objects — List all objects ───────────────────────────────────────

  router.get('/', (_req: Request, res: Response) => {
    const objects = metadata.getAllObjects();
    const result = objects.map(obj => ({
      ...obj,
      replicas: metadata.getReplicasForObject(obj.object_id),
    }));
    res.json({ objects: result, count: result.length });
  });

  // ─── GET /objects/:key/metadata ────────────────────────────────────────────

  router.get('/:key(*)/metadata', (req: Request, res: Response) => {
    const key = req.params.key;
    const obj = metadata.getObjectByKey(key);

    if (!obj) {
      res.status(404).json({ error: 'Object not found', key });
      return;
    }

    const replicas = metadata.getReplicasForObject(obj.object_id);

    res.json({
      ...obj,
      replicas,
    });
  });

  // ─── GET /objects/:key ─────────────────────────────────────────────────────

  /**
   * Retrieve an object by key.
   *
   * Read flow:
   *   1. Look up object in metadata
   *   2. Get healthy replicas
   *   3. Query R replicas in parallel via Coordinator
   *   4. Verify checksum on each response
   *   5. Return first valid response
   *   6. If a replica has a bad checksum → mark CORRUPT → trigger repair
   */
  router.get('/:key(*)', async (req: Request, res: Response) => {
    const key = req.params.key;
    const obj = metadata.getObjectByKey(key);

    if (!obj) {
      res.status(404).json({ error: 'Object not found', key });
      return;
    }

    const allNodes = metadata.getAllNodes();
    const nodeMap = new Map(allNodes.map(n => [n.node_id, n]));
    const healthyReplicas = metadata.getHealthyReplicasForObject(obj.object_id);
    const readableNodes = allNodes.filter(n =>
      n.state === 'HEALTHY' || n.state === 'SUSPECTED' || n.state === 'DRAINING'
    );

    const result = await coordinator.readQuorum(
      obj.object_id,
      obj.checksum,
      healthyReplicas,
      readableNodes,
      config.readQuorum
    );

    if (!result.success || !result.data) {
      res.status(503).json({
        error: 'Read quorum not achieved',
        required: config.readQuorum,
        available_replicas: healthyReplicas.length,
      });
      return;
    }

    metadata.appendEvent('OBJECT_READ', `Object "${key}" read from node ${result.sourceNodeId}`, {
      object_id: obj.object_id,
      key,
    });

    res
      .set('X-Object-Id', obj.object_id)
      .set('X-Object-Version', String(obj.version))
      .set('X-Object-Checksum', obj.checksum)
      .set('X-Vault-Version', String(obj.version))
      .set('X-Vault-Checksum', obj.checksum)
      .set('Content-Type', 'application/octet-stream')
      .send(result.data);
  });

  // ─── DELETE /objects/:key ──────────────────────────────────────────────────

  router.delete('/:key(*)', async (req: Request, res: Response) => {
    const key = req.params.key;
    const obj = metadata.getObjectByKey(key);

    if (!obj) {
      res.status(404).json({ error: 'Object not found', key });
      return;
    }

    const allNodes = metadata.getAllNodes();
    const nodeMap = new Map(allNodes.map(n => [n.node_id, n]));
    const replicas = metadata.getReplicasForObject(obj.object_id);

    // Soft-delete: mark as DELETED in metadata first
    metadata.deleteObject(obj.object_id);

    // Then delete from all nodes (best-effort)
    const deletedNodes = await coordinator.deleteFromNodes(obj.object_id, replicas, nodeMap);

    res.json({
      object_id: obj.object_id,
      key,
      deleted: true,
      nodes_cleaned: deletedNodes.length,
    });
  });

  return router;
}
