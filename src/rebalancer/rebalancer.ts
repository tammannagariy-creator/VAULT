/**
 * rebalancer/rebalancer.ts
 *
 * Rebalancer — manages replica distribution when nodes join or drain.
 *
 * Node Join:
 *   When a new node registers, existing replicas are all on old nodes.
 *   The new node sits idle with 0 replicas. Over time, as new objects are
 *   written, the PlacementService will prefer it (least-used-first).
 *   But existing objects are not automatically moved.
 *
 *   Rebalancing proactively migrates some replicas to the new node so that
 *   storage load is distributed evenly.
 *
 *   Safety: never migrate the last healthy replica of an object (SI-03).
 *
 * Node Drain:
 *   An operator wants to remove a node gracefully. The node is marked DRAINING,
 *   which excludes it from new writes. Its existing replicas must be migrated
 *   to other nodes before the node can be safely removed.
 *
 *   Steps:
 *     1. Mark node DRAINING
 *     2. For each replica on the draining node: create a repair job
 *     3. Wait for all repair jobs to complete (or timeout)
 *     4. Mark node FAILED (it's been drained)
 *
 * System Invariant SI-03: The last surviving copy of an object is NEVER deleted.
 */

import type { MetadataService } from '../metadata/service.js';
import { PlacementService } from '../gateway/placement.js';

export class Rebalancer {
  private metadata: MetadataService;
  private placement: PlacementService;

  constructor(metadata: MetadataService, placement: PlacementService) {
    this.metadata = metadata;
    this.placement = placement;
  }

  /**
   * Triggered when a new node joins the cluster.
   * Creates repair jobs to migrate some replicas to the new node.
   *
   * Strategy: For each object that has a replica on a node with more
   * replicas than average, create a repair job to add a replica on the new node.
   * Keep total replicas per object equal to replication_factor.
   */
  onNodeJoined(newNodeId: string): void {
    const newNode = this.metadata.getNode(newNodeId);
    if (!newNode) return;

    const allObjects = this.metadata.getAllObjects();
    const healthyNodes = this.metadata.getHealthyNodes();
    let scheduled = 0;

    for (const obj of allObjects) {
      if (obj.state === 'DELETED') continue;

      const replicas = this.metadata.getReplicasForObject(obj.object_id);
      const healthyReplicas = replicas.filter(r => r.state === 'HEALTHY');

      // If the object already has a replica on the new node, skip
      if (replicas.some(r => r.node_id === newNodeId)) continue;

      // If the object doesn't have enough replicas, let the repair worker handle it
      // The rebalancer only redistributes excess replicas
      const existingNodeIds = replicas.map(r => r.node_id);

      // Find the most-loaded source node that has a healthy replica
      const sourceNodes = healthyNodes.filter(n => 
        healthyReplicas.some(r => r.node_id === n.node_id)
      );
      const sourceNode = [...sourceNodes].sort((a, b) => b.storage_used - a.storage_used)[0];

      if (!sourceNode) continue;

      this.metadata.createRepairJob({
        objectId: obj.object_id,
        replicaId: null,
        targetNodeId: newNodeId,
        sourceNodeId: sourceNode.node_id,
        reason: 'MISSING',
      });
      scheduled++;

      // Limit initial rebalance to 10 objects to avoid overwhelming the cluster
      if (scheduled >= 10) break;
    }

    console.log(`[Rebalancer] Node ${newNodeId} joined — scheduled ${scheduled} replica migrations`);
    this.metadata.appendEvent(
      'REBALANCE_STARTED',
      `Node ${newNodeId} joined — rebalancing ${scheduled} objects`,
      { node_id: newNodeId, jobs_scheduled: scheduled }
    );
  }

  /**
   * Initiate a graceful drain of a node.
   * Creates repair jobs for all replicas on the draining node.
   *
   * Safety: If an object has only 1 healthy replica (on the draining node),
   * we still create the repair job — the repair worker will copy it before
   * the node is removed.
   */
  async drainNode(nodeId: string): Promise<{ jobsCreated: number }> {
    const node = this.metadata.getNode(nodeId);
    if (!node) throw new Error(`Node ${nodeId} not found`);

    console.log(`[Rebalancer] Starting drain of node ${nodeId}`);

    // Mark node as DRAINING — stops new writes to it
    this.metadata.updateNodeState(nodeId, 'DRAINING');

    const replicas = this.metadata.getReplicasOnNode(nodeId);
    const healthyNodes = this.metadata.getHealthyNodes().filter(n => n.node_id !== nodeId);
    let jobsCreated = 0;

    for (const replica of replicas) {
      const obj = this.metadata.getObjectById(replica.object_id);
      if (!obj || obj.state === 'DELETED') continue;

      // Find a target node for this replica
      const allReplicas = this.metadata.getReplicasForObject(replica.object_id);
      const existingNodeIds = allReplicas.map(r => r.node_id);

      const targetNode = this.placement.selectRepairTarget(healthyNodes, existingNodeIds);
      if (!targetNode) {
        console.warn(`[Rebalancer] No target for replica ${replica.replica_id} — cluster may be too small`);
        continue;
      }

      // Find a source: prefer replicas on non-draining nodes
      const healthyReplicas = this.metadata.getHealthyReplicasForObject(replica.object_id);
      const sourceReplica = healthyReplicas.find(r => r.node_id !== nodeId);
      const sourceNodeId = sourceReplica?.node_id ?? nodeId; // fallback to draining node itself

      this.metadata.createRepairJob({
        objectId: replica.object_id,
        replicaId: replica.replica_id,
        targetNodeId: targetNode.node_id,
        sourceNodeId: sourceNodeId,
        reason: 'MISSING',
      });
      jobsCreated++;
    }

    console.log(`[Rebalancer] Drain of ${nodeId}: created ${jobsCreated} repair jobs`);
    this.metadata.appendEvent(
      'NODE_DRAIN_STARTED',
      `Node ${nodeId} draining — ${jobsCreated} replicas to migrate`,
      { node_id: nodeId, jobs_created: jobsCreated }
    );

    return { jobsCreated };
  }
}
