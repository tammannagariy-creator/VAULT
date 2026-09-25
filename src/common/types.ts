/**
 * common/types.ts
 *
 * Shared TypeScript types for the entire Vault system.
 * These are the canonical definitions used by every component.
 */

// ─── Node State Machine ──────────────────────────────────────────────────────
// HEALTHY      → node is reachable and responding to heartbeats
// SUSPECTED    → one or more heartbeats missed; still serving reads/writes
// FAILED       → heartbeat timeout exceeded; excluded from new writes
// DRAINING     → operator requested graceful removal; no new writes
// RECOVERING   → previously failed node reconnected; re-syncing
export type NodeState = 'HEALTHY' | 'SUSPECTED' | 'FAILED' | 'DRAINING' | 'RECOVERING';

// ─── Object State Machine ─────────────────────────────────────────────────────
// DURABLE          → all replicas healthy; fully available
// UNDER_REPLICATED → fewer than replication_factor healthy replicas
// DELETED          → tombstoned; data may still exist on nodes pending cleanup
// PENDING          → write in progress; not yet committed
export type ObjectState = 'DURABLE' | 'UNDER_REPLICATED' | 'DELETED' | 'PENDING';

// ─── Replica State Machine ────────────────────────────────────────────────────
// HEALTHY  → replica verified and correct
// CORRUPT  → checksum mismatch detected
// MISSING  → expected replica not found on node
// STALE    → replica version is behind current object version
export type ReplicaState = 'HEALTHY' | 'CORRUPT' | 'MISSING' | 'STALE';

// ─── Repair Job State Machine ─────────────────────────────────────────────────
// PENDING    → job created; waiting to be picked up
// REPAIRING  → copying data from source node to target node
// VERIFYING  → verifying checksum + version of newly written replica
// DONE       → repair complete; replica is healthy
// FAILED     → repair could not be completed (logged; will retry)
export type RepairJobState = 'PENDING' | 'REPAIRING' | 'VERIFYING' | 'DONE' | 'FAILED';

// ─── Domain Models ────────────────────────────────────────────────────────────

export interface StorageNode {
  node_id: string;
  address: string;
  port: number;
  state: NodeState;
  last_heartbeat: string | null;
  storage_used: number;   // bytes
  storage_total: number;  // bytes (0 = unknown)
  registered_at: string;
}

export interface ObjectMetadata {
  object_id: string;
  logical_key: string;    // the user-facing key, e.g. "reports/2024/q1.pdf"
  version: number;        // monotonic integer, incremented on every PUT
  size: number;           // bytes
  checksum: string;       // "sha256:<hex>"
  replication_factor: number;
  placement_epoch: number; // cluster epoch when placed; used to detect stale placement
  state: ObjectState;
  created_at: string;     // ISO 8601
  updated_at: string;
}

export interface ReplicaMetadata {
  replica_id: string;
  object_id: string;
  node_id: string;
  version: number;        // version of the object this replica holds
  checksum: string;
  size: number;
  state: ReplicaState;
  last_verified_at: string | null;
  created_at: string;
}

export interface RepairJob {
  job_id: string;
  object_id: string;
  replica_id: string | null; // null when a replica is missing entirely
  target_node_id: string;    // node that will receive the new replica
  source_node_id: string;    // node that the data will be copied from
  state: RepairJobState;
  reason: string;            // "MISSING" | "CORRUPT" | "STALE"
  created_at: string;
  updated_at: string;
}

export interface VaultEvent {
  event_id: string;
  type: string;           // e.g. "NODE_FAILED", "REPAIR_STARTED", "CORRUPT_DETECTED"
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

// ─── Internal API Types ───────────────────────────────────────────────────────
// These are used for internal gateway ↔ storage-node communication.

export interface StoreWriteRequest {
  object_id: string;
  version: number;
  checksum: string;
  size: number;
  // actual bytes sent as raw body
}

export interface StoreReadResponse {
  object_id: string;
  version: number;
  checksum: string;
  size: number;
  // actual bytes in response body
}

export interface NodeHeartbeatRequest {
  node_id: string;
  address: string;
  port: number;
  storage_used: number;
  storage_total: number;
}

export interface QuorumWriteResult {
  success: boolean;
  ackCount: number;
  failures: string[]; // node_ids that failed
}

export interface QuorumReadResult {
  success: boolean;
  data: Buffer | null;
  checksum: string;
  version: number;
  sourceNodeId: string;
}

export interface ClusterStatus {
  nodes: StorageNode[];
  totalObjects: number;
  durableObjects: number;
  underReplicatedObjects: number;
  totalReplicas: number;
  healthyReplicas: number;
  corruptReplicas: number;
  pendingRepairJobs: number;
  recentEvents: VaultEvent[];
}
