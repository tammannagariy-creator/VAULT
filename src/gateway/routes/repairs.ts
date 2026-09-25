/**
 * gateway/routes/repairs.ts
 *
 * Repair job management APIs:
 *   GET  /repairs           — list all repair jobs
 *   GET  /repairs/:id       — get a specific repair job
 *   POST /repairs/trigger   — manually trigger repair scan (for demo)
 */

import { Router, Request, Response } from 'express';
import type { MetadataService } from '../../metadata/service.js';
import type { RepairWorker } from '../../repair/worker.js';

export function repairsRouter(metadata: MetadataService, repairWorker: RepairWorker): Router {
  const router = Router();

  // ─── GET /repairs ─────────────────────────────────────────────────────────

  router.get('/', (req: Request, res: Response) => {
    const limit = Math.min(parseInt(String(req.query.limit ?? '50'), 10), 200);
    const jobs = metadata.getAllRepairJobs(limit);
    res.json({ jobs, count: jobs.length });
  });

  // ─── POST /repairs/trigger — manually trigger repair scan (demo tool) ─────

  router.post('/trigger', (_req: Request, res: Response) => {
    // Force the repair worker to scan immediately
    const underReplicated = metadata.getUnderReplicatedObjects();
    let triggered = 0;

    for (const obj of underReplicated) {
      const healthyReplicas = metadata.getHealthyReplicasForObject(obj.object_id);
      const allNodes = metadata.getAllNodes();
      const healthyNodes = metadata.getHealthyNodes();

      if (healthyReplicas.length === 0) continue;

      const existingNodeIds = metadata.getReplicasForObject(obj.object_id).map(r => r.node_id);
      const targetNode = healthyNodes.find(n => !existingNodeIds.includes(n.node_id));
      const sourceNode = allNodes.find(n => healthyReplicas.some(r => r.node_id === n.node_id));

      if (!targetNode || !sourceNode) continue;

      metadata.createRepairJob({
        objectId: obj.object_id,
        replicaId: null,
        targetNodeId: targetNode.node_id,
        sourceNodeId: sourceNode.node_id,
        reason: 'MISSING',
      });
      triggered++;
    }

    res.json({
      triggered,
      under_replicated_objects: underReplicated.length,
      message: `Triggered ${triggered} repair job(s)`,
    });
  });

  return router;
}
