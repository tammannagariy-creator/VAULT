/**
 * membership/detector.ts
 *
 * FailureDetector — tracks storage node health via heartbeats.
 *
 * State machine:
 *   HEALTHY   → receives heartbeats within timeout
 *   SUSPECTED → missed 1+ heartbeats; might be slow network — still serves data
 *   FAILED    → timeout exceeded; excluded from new writes; repair triggered
 *   RECOVERING → node re-registered; first heartbeat transitions back to HEALTHY
 *   DRAINING  → operator request; no new writes; replicas migrating
 *
 * Why "SUSPECTED" before "FAILED"?
 *   A node might miss a heartbeat due to a slow network or GC pause, not a crash.
 *   Immediately marking it FAILED and triggering repair wastes resources.
 *   The SUSPECTED state gives the node a grace period to recover.
 *
 * System Invariant SI-07: A SUSPECTED node continues serving reads and writes.
 * System Invariant SI-08: A FAILED node is excluded from new placement decisions.
 */

import type { MetadataService } from '../metadata/service.js';

interface FailureDetectorConfig {
  heartbeatTimeout: number;  // ms before SUSPECTED → FAILED
  checkInterval: number;     // ms between checks
}

export class FailureDetector {
  private metadata: MetadataService;
  private config: FailureDetectorConfig;
  private timer: ReturnType<typeof setInterval> | null = null;

  // Callbacks to notify the repair worker when a node fails
  private onNodeFailed: ((nodeId: string) => void)[] = [];

  constructor(metadata: MetadataService, config: FailureDetectorConfig) {
    this.metadata = metadata;
    this.config = config;
  }

  /** Register a callback to be called when a node transitions to FAILED */
  onFailure(callback: (nodeId: string) => void): void {
    this.onNodeFailed.push(callback);
  }

  start(): void {
    console.log(`[FailureDetector] Starting (timeout: ${this.config.heartbeatTimeout}ms)`);
    this.timer = setInterval(() => this.checkNodes(), this.config.checkInterval);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private checkNodes(): void {
    const nodes = this.metadata.getAllNodes();
    const now = Date.now();

    for (const node of nodes) {
      if (node.state === 'DRAINING' || node.state === 'FAILED') continue;

      const lastHeartbeat = node.last_heartbeat
        ? new Date(node.last_heartbeat).getTime()
        : 0;
      const elapsed = now - lastHeartbeat;

      if (elapsed > this.config.heartbeatTimeout) {
        // Timeout exceeded: mark as FAILED
        console.warn(
          `[FailureDetector] Node ${node.node_id} FAILED — no heartbeat for ${Math.round(elapsed / 1000)}s`
        );
        this.metadata.updateNodeState(node.node_id, 'FAILED');

        // Mark all of this node's replicas as MISSING
        this.metadata.markNodeReplicasMissing(node.node_id);

        // Notify the repair worker
        this.onNodeFailed.forEach(cb => cb(node.node_id));

        // Find all objects that are now under-replicated
        this.detectUnderReplicated(node.node_id);
      } else if (elapsed > this.config.heartbeatTimeout / 2 && node.state === 'HEALTHY') {
        // Half-timeout: become SUSPECTED
        console.warn(
          `[FailureDetector] Node ${node.node_id} SUSPECTED — no heartbeat for ${Math.round(elapsed / 1000)}s`
        );
        this.metadata.updateNodeState(node.node_id, 'SUSPECTED');
      } else if (node.state === 'SUSPECTED') {
        // Heartbeat received → recover
        this.metadata.updateNodeState(node.node_id, 'HEALTHY');
      }
    }
  }

  private detectUnderReplicated(failedNodeId: string): void {
    // Get all replicas on the failed node
    const failedReplicas = this.metadata.getReplicasOnNode(failedNodeId);

    for (const replica of failedReplicas) {
      // Recalculate replication state for this object
      this.metadata.refreshObjectReplicationState(replica.object_id);
    }
  }
}
