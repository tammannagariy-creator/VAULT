/**
 * repair/worker.ts
 *
 * RepairWorker — background process that detects and fixes under-replicated objects.
 *
 * Problem it solves:
 *   When a storage node fails, all objects that had a replica on that node
 *   become "under-replicated". The system now has fewer than N copies of those
 *   objects, violating the durability guarantee.
 *
 * How it works:
 *   1. Runs on a configurable interval (default: 10 seconds)
 *   2. Queries metadata for PENDING repair jobs
 *   3. For each job:
 *      a. Find a healthy source replica
 *      b. Find a healthy target node (that doesn't already have a copy)
 *      c. Copy the data from source to target
 *      d. Verify the checksum of the copy
 *      e. Update metadata to add the new replica
 *      f. Mark the object DURABLE if it now has enough replicas
 *
 * Repair operations are idempotent:
 *   Running the same repair job twice is safe. The upsert in MetadataService.addReplica()
 *   handles this. If the job fails partway through, the next run restarts from PENDING.
 *
 * System Invariant SI-09: Repair jobs are idempotent.
 * System Invariant SI-10: Tombstoned (deleted) objects are never repaired.
 * System Invariant SI-04: Repair never overwrites a newer version with an older one.
 */

import type { MetadataService } from '../metadata/service.js';
import { Coordinator } from '../gateway/coordinator.js';
import { PlacementService } from '../gateway/placement.js';

interface RepairWorkerConfig {
  repairInterval: number;
}

export class RepairWorker {
  private metadata: MetadataService;
  private coordinator: Coordinator;
  private placement: PlacementService;
  private config: RepairWorkerConfig;
  private timer: ReturnType<typeof setInterval> | null = null;
  private isRunning = false;

  constructor(
    metadata: MetadataService,
    coordinator: Coordinator,
    placement: PlacementService,
    config: RepairWorkerConfig
  ) {
    this.metadata = metadata;
    this.coordinator = coordinator;
    this.placement = placement;
    this.config = config;
  }

  start(): void {
    console.log(`[RepairWorker] Starting (interval: ${this.config.repairInterval}ms)`);
    this.timer = setInterval(() => this.runRepairCycle(), this.config.repairInterval);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  /**
   * Schedule repair jobs for all objects that became under-replicated
   * after a node failure.
   */
  scheduleRepairsForFailedNode(failedNodeId: string): void {
    const underReplicated = this.metadata.getUnderReplicatedObjects();
    let scheduled = 0;

    for (const obj of underReplicated) {
      // Skip deleted objects — Invariant SI-10
      if (obj.state === 'DELETED') continue;

      const healthyReplicas = this.metadata.getHealthyReplicasForObject(obj.object_id);
      const allReplicas = this.metadata.getReplicasForObject(obj.object_id);
      const allNodes = this.metadata.getAllNodes();
      const healthyNodes = this.metadata.getHealthyNodes();

      if (healthyReplicas.length === 0) {
        console.error(`[RepairWorker] Object ${obj.object_id} has NO healthy replicas — data may be lost`);
        continue;
      }

      // Determine which nodes already have a copy (healthy or otherwise)
      const existingNodeIds = allReplicas.map(r => r.node_id);

      // Select a target node
      const targetNode = this.placement.selectRepairTarget(healthyNodes, existingNodeIds);
      if (!targetNode) {
        console.warn(`[RepairWorker] No eligible target node for repairing object ${obj.object_id}`);
        continue;
      }

      // Select a source node (prefer least loaded)
      const sourceNodeIds = healthyReplicas.map(r => r.node_id);
      const sourceNodes = allNodes.filter(n => sourceNodeIds.includes(n.node_id));
      const sourceNode = this.placement.selectRepairSource(sourceNodes);
      if (!sourceNode) continue;

      this.metadata.createRepairJob({
        objectId: obj.object_id,
        replicaId: null,
        targetNodeId: targetNode.node_id,
        sourceNodeId: sourceNode.node_id,
        reason: 'MISSING',
      });
      scheduled++;
    }

    console.log(`[RepairWorker] Scheduled ${scheduled} repair jobs after node ${failedNodeId} failed`);
  }

  /**
   * Schedule a repair for a specific corrupt replica.
   * Called by the corruption detection path.
   */
  scheduleRepairForCorruptReplica(objectId: string, corruptNodeId: string, replicaId: string): void {
    const healthyReplicas = this.metadata.getHealthyReplicasForObject(objectId);
    const allReplicas = this.metadata.getReplicasForObject(objectId);
    const healthyNodes = this.metadata.getHealthyNodes();
    const allNodes = this.metadata.getAllNodes();

    if (healthyReplicas.length === 0) {
      console.error(`[RepairWorker] Object ${objectId} has no healthy replicas — cannot repair`);
      return;
    }

    const existingNodeIds = allReplicas.map(r => r.node_id);
    const targetNode = this.placement.selectRepairTarget(
      healthyNodes,
      existingNodeIds.filter(id => id !== corruptNodeId)
    ) ?? this.metadata.getNode(corruptNodeId); // reuse same node if no better option

    if (!targetNode) return;

    const sourceNodeIds = healthyReplicas.map(r => r.node_id);
    const sourceNodes = allNodes.filter(n => sourceNodeIds.includes(n.node_id));
    const sourceNode = this.placement.selectRepairSource(sourceNodes);
    if (!sourceNode) return;

    this.metadata.createRepairJob({
      objectId,
      replicaId,
      targetNodeId: targetNode.node_id,
      sourceNodeId: sourceNode.node_id,
      reason: 'CORRUPT',
    });
  }

  /**
   * Main repair loop — processes PENDING jobs.
   */
  private async runRepairCycle(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;

    const pendingJobs = this.metadata.getPendingRepairJobs();
    if (pendingJobs.length === 0) {
      this.isRunning = false;
      return;
    }

    console.log(`[RepairWorker] Processing ${pendingJobs.length} pending repair jobs`);

    for (const job of pendingJobs) {
      try {
        await this.executeRepairJob(job.job_id);
      } catch (err) {
        console.error(`[RepairWorker] Job ${job.job_id} threw an unexpected error:`, err);
        this.metadata.updateRepairJobState(job.job_id, 'FAILED');
      }
    }

    this.isRunning = false;
  }

  private async executeRepairJob(jobId: string): Promise<void> {
    const jobs = this.metadata.getAllRepairJobs(100);
    const job = jobs.find(j => j.job_id === jobId);
    if (!job) return;

    // Skip if the object was deleted while the job was queued
    const obj = this.metadata.getObjectById(job.object_id);
    if (!obj || obj.state === 'DELETED') {
      this.metadata.updateRepairJobState(jobId, 'DONE');
      return;
    }

    const allNodes = this.metadata.getAllNodes();
    const nodeMap = new Map(allNodes.map(n => [n.node_id, n]));
    const sourceNode = nodeMap.get(job.source_node_id);
    const targetNode = nodeMap.get(job.target_node_id);

    if (!sourceNode || sourceNode.state === 'FAILED') {
      // Source is no longer available — try to find a new source
      const healthyReplicas = this.metadata.getHealthyReplicasForObject(job.object_id);
      const newSourceNode = this.placement.selectRepairSource(
        allNodes.filter(n => healthyReplicas.some(r => r.node_id === n.node_id))
      );
      if (!newSourceNode) {
        console.error(`[RepairWorker] Job ${jobId}: no healthy source found, marking FAILED`);
        this.metadata.updateRepairJobState(jobId, 'FAILED');
        return;
      }
      // Update the job's source node in metadata would require a DB update;
      // for simplicity, just use the new source directly
      await this.doRepair(jobId, obj, newSourceNode, targetNode!, nodeMap);
      return;
    }

    if (!targetNode || targetNode.state === 'FAILED') {
      console.error(`[RepairWorker] Job ${jobId}: target node ${job.target_node_id} is FAILED`);
      this.metadata.updateRepairJobState(jobId, 'FAILED');
      return;
    }

    await this.doRepair(jobId, obj, sourceNode, targetNode, nodeMap);
  }

  private async doRepair(
    jobId: string,
    obj: { object_id: string; checksum: string; version: number; size: number; replication_factor: number },
    sourceNode: { node_id: string; address: string; port: number },
    targetNode: { node_id: string; address: string; port: number },
    nodeMap: Map<string, { node_id: string; address: string; port: number; state: string; storage_used: number; storage_total: number; last_heartbeat: string | null; registered_at: string }>
  ): Promise<void> {
    console.log(
      `[RepairWorker] Job ${jobId}: copying object ${obj.object_id} ` +
      `from ${sourceNode.node_id} → ${targetNode.node_id}`
    );

    // REPAIRING
    this.metadata.updateRepairJobState(jobId, 'REPAIRING');

    const success = await this.coordinator.copyReplica(
      obj.object_id,
      obj.version,
      obj.checksum,
      sourceNode as Parameters<typeof this.coordinator.copyReplica>[4],
      targetNode as Parameters<typeof this.coordinator.copyReplica>[4]
    );

    if (!success) {
      this.metadata.updateRepairJobState(jobId, 'FAILED');
      return;
    }

    // VERIFYING
    this.metadata.updateRepairJobState(jobId, 'VERIFYING');

    // Add the new replica to metadata
    this.metadata.addReplica({
      objectId: obj.object_id,
      nodeId: targetNode.node_id,
      version: obj.version,
      checksum: obj.checksum,
      size: obj.size,
    });

    // Recalculate object state
    this.metadata.refreshObjectReplicationState(obj.object_id);

    // DONE
    this.metadata.updateRepairJobState(jobId, 'DONE');
    console.log(`[RepairWorker] Job ${jobId}: repair DONE for object ${obj.object_id}`);
  }
}
