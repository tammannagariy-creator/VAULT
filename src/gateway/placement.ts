/**
 * gateway/placement.ts
 *
 * PlacementService — decides which healthy nodes will hold replicas
 * of a newly written object.
 *
 * Strategy: Least-used-first
 *   Select N healthy nodes, sorted by storage_used ascending.
 *   This naturally balances storage load across nodes without
 *   requiring a separate rebalancing trigger on every write.
 *
 * If fewer than N healthy nodes are available, we return all that
 * are available and let the Coordinator decide whether quorum can be met.
 *
 * Design Decision:
 *   We do NOT use consistent hashing for the hackathon scope. 
 *   Least-used-first is simpler, demonstrable, and correct.
 *   Consistent hashing would be an "Advanced" feature.
 */

import type { StorageNode } from '../common/types.js';

export class PlacementService {
  /**
   * Select N nodes to hold replicas of a new object.
   *
   * @param healthyNodes - all nodes with state === 'HEALTHY'
   * @param replicationFactor - how many nodes to select
   * @param excludeNodeIds - nodes to exclude (e.g., nodes that already have a replica)
   */
  selectNodes(
    healthyNodes: StorageNode[],
    replicationFactor: number,
    excludeNodeIds: string[] = []
  ): StorageNode[] {
    const candidates = healthyNodes
      .filter(n => !excludeNodeIds.includes(n.node_id))
      .sort((a, b) => a.storage_used - b.storage_used); // least-used first

    return candidates.slice(0, replicationFactor);
  }

  /**
   * Select the best node to hold a replacement replica during repair.
   * Same logic as selectNodes but limited to 1 node.
   */
  selectRepairTarget(
    healthyNodes: StorageNode[],
    excludeNodeIds: string[]
  ): StorageNode | null {
    const candidates = this.selectNodes(healthyNodes, 1, excludeNodeIds);
    return candidates[0] ?? null;
  }

  /**
   * Select the best source node for a repair operation.
   * Prefer nodes with low storage pressure (so the read doesn't strain a busy node).
   *
   * @param candidates - nodes that have a healthy replica of the object
   */
  selectRepairSource(candidates: StorageNode[]): StorageNode | null {
    if (candidates.length === 0) return null;
    return [...candidates].sort((a, b) => a.storage_used - b.storage_used)[0];
  }
}
