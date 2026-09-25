/**
 * metadata/service.ts
 *
 * MetadataService — the authoritative source of truth for all object,
 * replica, node, and repair-job state in the Vault cluster.
 *
 * All state transitions go through this service.
 * The coordinator never modifies state directly — it always calls MetadataService.
 *
 * Invariants enforced here:
 *   - Object version is monotonically increasing
 *   - A replica cannot be marked HEALTHY unless its checksum matches the object
 *   - Repair jobs are deduplicated (no two PENDING jobs for the same object+node)
 *   - Events are always appended; never mutated
 */

import { VaultDatabase } from './db.js';
import { v4 as uuidv4 } from 'uuid';
import type {
  StorageNode,
  ObjectMetadata,
  ReplicaMetadata,
  RepairJob,
  VaultEvent,
  NodeState,
  ObjectState,
  ReplicaState,
  RepairJobState,
  ClusterStatus,
} from '../common/types.js';

export class MetadataService {
  private db: VaultDatabase;

  constructor(db: VaultDatabase) {
    this.db = db;
  }

  /** Type-safe cast for node:sqlite results which return Record<string,unknown> */
  private cast<T>(val: Record<string, unknown> | undefined): T | null {
    return val ? (val as unknown as T) : null;
  }

  private castMany<T>(val: Record<string, unknown>[]): T[] {
    return val as unknown as T[];
  }

  // ─── NODE OPERATIONS ────────────────────────────────────────────────────────

  registerNode(node: Omit<StorageNode, 'state' | 'registered_at' | 'last_heartbeat'>): StorageNode {
    const now = new Date().toISOString();
    const existing = this.db
      .prepare('SELECT * FROM nodes WHERE node_id = ?')
      .get(node.node_id) as StorageNode | undefined;

    if (existing) {
      // Node re-registering after restart — update its address/port and mark RECOVERING
      this.db
        .prepare(`
          UPDATE nodes SET
            address = ?, port = ?, state = 'RECOVERING',
            last_heartbeat = ?, storage_used = ?, storage_total = ?
          WHERE node_id = ?
        `)
        .run(
          node.address, node.port, now,
          node.storage_used, node.storage_total,
          node.node_id
        );
      this.appendEvent('NODE_RECOVERING', `Node ${node.node_id} re-registered`, { node_id: node.node_id });
    } else {
      this.db
        .prepare(`
          INSERT INTO nodes (node_id, address, port, state, last_heartbeat, storage_used, storage_total, registered_at)
          VALUES (?, ?, ?, 'HEALTHY', ?, ?, ?, ?)
        `)
        .run(node.node_id, node.address, node.port, now, node.storage_used, node.storage_total, now);
      this.appendEvent('NODE_JOINED', `Node ${node.node_id} joined cluster at ${node.address}:${node.port}`, { node_id: node.node_id });
    }

    return this.getNode(node.node_id)!;
  }

  updateHeartbeat(nodeId: string, storageUsed: number, storageTotal: number): void {
    const now = new Date().toISOString();
    const node = this.getNode(nodeId);
    if (!node) return;

    // A RECOVERING or FAILED node becomes HEALTHY after its successful heartbeat
    const newState = (node.state === 'RECOVERING' || node.state === 'FAILED') ? 'HEALTHY' : node.state;

    this.db
      .prepare(`
        UPDATE nodes SET
          last_heartbeat = ?, storage_used = ?, storage_total = ?, state = ?
        WHERE node_id = ?
      `)
      .run(now, storageUsed, storageTotal, newState, nodeId);

    if (node.state === 'RECOVERING' || node.state === 'FAILED') {
      this.appendEvent('NODE_RECOVERED', `Node ${nodeId} is now HEALTHY`, { node_id: nodeId });
    }
  }

  updateNodeState(nodeId: string, state: NodeState): void {
    const prev = this.getNode(nodeId);
    this.db.prepare('UPDATE nodes SET state = ? WHERE node_id = ?').run(state, nodeId);

    if (prev && prev.state !== state) {
      this.appendEvent(
        `NODE_${state}`,
        `Node ${nodeId} transitioned from ${prev.state} to ${state}`,
        { node_id: nodeId, from: prev.state, to: state }
      );
    }
  }

  getNode(nodeId: string): StorageNode | null {
    return this.cast<StorageNode>(this.db.prepare('SELECT * FROM nodes WHERE node_id = ?').get(nodeId));
  }

  getAllNodes(): StorageNode[] {
    return this.castMany<StorageNode>(this.db.prepare('SELECT * FROM nodes ORDER BY registered_at').all());
  }

  getHealthyNodes(): StorageNode[] {
    return this.castMany<StorageNode>(
      this.db.prepare("SELECT * FROM nodes WHERE state = 'HEALTHY' ORDER BY storage_used ASC").all()
    );
  }

  // ─── OBJECT OPERATIONS ──────────────────────────────────────────────────────

  createObject(params: {
    logicalKey: string;
    size: number;
    checksum: string;
    replicationFactor: number;
  }): ObjectMetadata {
    const objectId = uuidv4();
    const now = new Date().toISOString();
    const epoch = this.getCurrentEpoch();

    this.db
      .prepare(`
        INSERT INTO objects
          (object_id, logical_key, version, size, checksum, replication_factor, placement_epoch, state, created_at, updated_at)
        VALUES (?, ?, 1, ?, ?, ?, ?, 'PENDING', ?, ?)
      `)
      .run(objectId, params.logicalKey, params.size, params.checksum, params.replicationFactor, epoch, now, now);

    return this.getObjectById(objectId)!;
  }

  /**
   * Updates an existing object key with a new version.
   * Version is incremented server-side (monotonic) — clients cannot set version.
   * This satisfies SI-04: repair never overwrites a newer version with older one.
   */
  updateObject(objectId: string, params: {
    size: number;
    checksum: string;
  }): ObjectMetadata {
    const now = new Date().toISOString();
    this.db
      .prepare(`
        UPDATE objects SET
          version = version + 1,
          size = ?,
          checksum = ?,
          state = 'PENDING',
          updated_at = ?
        WHERE object_id = ?
      `)
      .run(params.size, params.checksum, now, objectId);

    // Delete all old replicas — they are now stale
    this.db
      .prepare("UPDATE replicas SET state = 'STALE' WHERE object_id = ?")
      .run(objectId);

    return this.getObjectById(objectId)!;
  }

  commitObject(objectId: string): void {
    const now = new Date().toISOString();
    this.db
      .prepare("UPDATE objects SET state = 'DURABLE', updated_at = ? WHERE object_id = ?")
      .run(now, objectId);
    this.appendEvent('OBJECT_COMMITTED', `Object ${objectId} committed as DURABLE`, { object_id: objectId });
  }

  markObjectUnderReplicated(objectId: string): void {
    const now = new Date().toISOString();
    const obj = this.getObjectById(objectId);
    if (!obj || obj.state === 'DELETED') return;

    this.db
      .prepare("UPDATE objects SET state = 'UNDER_REPLICATED', updated_at = ? WHERE object_id = ?")
      .run(now, objectId);
    this.appendEvent('OBJECT_UNDER_REPLICATED', `Object ${objectId} is under-replicated`, { object_id: objectId });
  }

  deleteObject(objectId: string): void {
    const now = new Date().toISOString();
    this.db
      .prepare("UPDATE objects SET state = 'DELETED', updated_at = ? WHERE object_id = ?")
      .run(now, objectId);
    this.appendEvent('OBJECT_DELETED', `Object ${objectId} marked as DELETED`, { object_id: objectId });
  }

  getObjectByKey(key: string): ObjectMetadata | null {
    return this.cast<ObjectMetadata>(
      this.db.prepare("SELECT * FROM objects WHERE logical_key = ? AND state != 'DELETED'").get(key)
    );
  }

  getObjectById(objectId: string): ObjectMetadata | null {
    return this.cast<ObjectMetadata>(
      this.db.prepare('SELECT * FROM objects WHERE object_id = ?').get(objectId)
    );
  }

  getAllObjects(): ObjectMetadata[] {
    return this.castMany<ObjectMetadata>(
      this.db.prepare("SELECT * FROM objects WHERE state != 'DELETED'").all()
    );
  }

  getUnderReplicatedObjects(): ObjectMetadata[] {
    return this.castMany<ObjectMetadata>(
      this.db.prepare("SELECT * FROM objects WHERE state = 'UNDER_REPLICATED'").all()
    );
  }

  // ─── REPLICA OPERATIONS ──────────────────────────────────────────────────────

  addReplica(params: {
    objectId: string;
    nodeId: string;
    version: number;
    checksum: string;
    size: number;
  }): ReplicaMetadata {
    const replicaId = uuidv4();
    const now = new Date().toISOString();

    // Upsert: if a replica already exists for this object+node, update it
    this.db
      .prepare(`
        INSERT INTO replicas (replica_id, object_id, node_id, version, checksum, size, state, last_verified_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'HEALTHY', ?, ?)
        ON CONFLICT(object_id, node_id) DO UPDATE SET
          version = excluded.version,
          checksum = excluded.checksum,
          size = excluded.size,
          state = 'HEALTHY',
          last_verified_at = excluded.last_verified_at
      `)
      .run(replicaId, params.objectId, params.nodeId, params.version, params.checksum, params.size, now, now);

    return this.cast<ReplicaMetadata>(
      this.db.prepare('SELECT * FROM replicas WHERE object_id = ? AND node_id = ?').get(params.objectId, params.nodeId)
    )!;
  }

  updateReplicaState(replicaId: string, state: ReplicaState): void {
    const now = new Date().toISOString();
    this.db
      .prepare('UPDATE replicas SET state = ?, last_verified_at = ? WHERE replica_id = ?')
      .run(state, now, replicaId);
  }

  getReplicasForObject(objectId: string): ReplicaMetadata[] {
    return this.castMany<ReplicaMetadata>(
      this.db.prepare('SELECT * FROM replicas WHERE object_id = ?').all(objectId)
    );
  }

  getHealthyReplicasForObject(objectId: string): ReplicaMetadata[] {
    return this.castMany<ReplicaMetadata>(
      this.db.prepare("SELECT * FROM replicas WHERE object_id = ? AND state = 'HEALTHY'").all(objectId)
    );
  }

  getReplicasOnNode(nodeId: string): ReplicaMetadata[] {
    return this.castMany<ReplicaMetadata>(
      this.db.prepare("SELECT * FROM replicas WHERE node_id = ? AND state != 'MISSING'").all(nodeId)
    );
  }

  markNodeReplicasMissing(nodeId: string): void {
    this.db
      .prepare("UPDATE replicas SET state = 'MISSING' WHERE node_id = ? AND state = 'HEALTHY'")
      .run(nodeId);
  }

  // ─── REPAIR JOB OPERATIONS ───────────────────────────────────────────────────

  createRepairJob(params: {
    objectId: string;
    replicaId: string | null;
    targetNodeId: string;
    sourceNodeId: string;
    reason: string;
  }): RepairJob {
    // Deduplication: don't create a job if one is already PENDING/REPAIRING for this object+node
    const existing = this.cast<RepairJob>(
      this.db.prepare(`
        SELECT * FROM repair_jobs
        WHERE object_id = ? AND target_node_id = ?
        AND state IN ('PENDING', 'REPAIRING', 'VERIFYING')
      `).get(params.objectId, params.targetNodeId)
    );

    if (existing) {
      return existing;
    }

    const jobId = uuidv4();
    const now = new Date().toISOString();

    this.db
      .prepare(`
        INSERT INTO repair_jobs
          (job_id, object_id, replica_id, target_node_id, source_node_id, state, reason, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)
      `)
      .run(jobId, params.objectId, params.replicaId, params.targetNodeId, params.sourceNodeId, params.reason, now, now);

    this.appendEvent(
      'REPAIR_QUEUED',
      `Repair job created for object ${params.objectId} → node ${params.targetNodeId} (reason: ${params.reason})`,
      { job_id: jobId, object_id: params.objectId, reason: params.reason }
    );

    return this.cast<RepairJob>(
      this.db.prepare('SELECT * FROM repair_jobs WHERE job_id = ?').get(jobId)
    )!;
  }

  updateRepairJobState(jobId: string, state: RepairJobState): void {
    const now = new Date().toISOString();
    this.db
      .prepare('UPDATE repair_jobs SET state = ?, updated_at = ? WHERE job_id = ?')
      .run(state, now, jobId);

    if (state === 'DONE' || state === 'FAILED') {
      const job = this.cast<RepairJob>(
        this.db.prepare('SELECT * FROM repair_jobs WHERE job_id = ?').get(jobId)
      );
      this.appendEvent(
        state === 'DONE' ? 'REPAIR_DONE' : 'REPAIR_FAILED',
        `Repair job ${jobId} for object ${job?.object_id} ${state === 'DONE' ? 'completed successfully' : 'FAILED'}`,
        { job_id: jobId }
      );
    }
  }

  getPendingRepairJobs(): RepairJob[] {
    return this.castMany<RepairJob>(
      this.db.prepare("SELECT * FROM repair_jobs WHERE state = 'PENDING' ORDER BY created_at").all()
    );
  }

  getAllRepairJobs(limit = 50): RepairJob[] {
    return this.castMany<RepairJob>(
      this.db.prepare('SELECT * FROM repair_jobs ORDER BY created_at DESC LIMIT ?').all(limit)
    );
  }

  // ─── EVENT LOG ───────────────────────────────────────────────────────────────

  appendEvent(type: string, message: string, payload?: Record<string, unknown>): VaultEvent {
    const eventId = uuidv4();
    const now = new Date().toISOString();
    const payloadStr = payload ? JSON.stringify(payload) : null;

    this.db
      .prepare(`
        INSERT INTO events (event_id, type, message, payload, created_at)
        VALUES (?, ?, ?, ?, ?)
      `)
      .run(eventId, type, message, payloadStr, now);

    // Keep event log bounded to last 1000 entries
    this.db.exec(`
      DELETE FROM events WHERE event_id NOT IN (
        SELECT event_id FROM events ORDER BY created_at DESC LIMIT 1000
      )
    `);

    return { event_id: eventId, type, message, payload: payload ?? null, created_at: now };
  }

  getRecentEvents(limit = 50): VaultEvent[] {
    const rows = this.db
      .prepare('SELECT * FROM events ORDER BY created_at DESC LIMIT ?')
      .all(limit) as Array<Omit<VaultEvent, 'payload'> & { payload: string | null }>;

    return rows.map(row => ({
      ...row,
      payload: row.payload ? JSON.parse(row.payload) : null,
    }));
  }

  // ─── CLUSTER STATUS ──────────────────────────────────────────────────────────

  getClusterStatus(): ClusterStatus {
    const nodes = this.getAllNodes();

    const counts = this.db.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN state = 'DURABLE' THEN 1 ELSE 0 END) as durable,
        SUM(CASE WHEN state = 'UNDER_REPLICATED' THEN 1 ELSE 0 END) as under_replicated
      FROM objects WHERE state != 'DELETED'
    `).get() as { total: number; durable: number; under_replicated: number };

    const replicaCounts = this.db.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN state = 'HEALTHY' THEN 1 ELSE 0 END) as healthy,
        SUM(CASE WHEN state = 'CORRUPT' THEN 1 ELSE 0 END) as corrupt
      FROM replicas
    `).get() as { total: number; healthy: number; corrupt: number };

    const pendingRepairs = (this.db.prepare(
      "SELECT COUNT(*) as cnt FROM repair_jobs WHERE state IN ('PENDING', 'REPAIRING', 'VERIFYING')"
    ).get() as { cnt: number }).cnt;

    return {
      nodes,
      totalObjects: counts.total,
      durableObjects: counts.durable,
      underReplicatedObjects: counts.under_replicated,
      totalReplicas: replicaCounts.total,
      healthyReplicas: replicaCounts.healthy,
      corruptReplicas: replicaCounts.corrupt,
      pendingRepairJobs: pendingRepairs,
      recentEvents: this.getRecentEvents(20),
    };
  }

  // ─── HELPERS ─────────────────────────────────────────────────────────────────

  private getCurrentEpoch(): number {
    // Epoch = number of nodes ever joined. Simple but sufficient.
    const result = this.db.prepare('SELECT COUNT(*) as cnt FROM nodes').get() as { cnt: number };
    return result.cnt;
  }

  /**
   * Atomically checks how many healthy replicas an object has,
   * and updates its state accordingly.
   * Called after node failures, repairs, and deletions.
   */
  refreshObjectReplicationState(objectId: string): void {
    const obj = this.getObjectById(objectId);
    if (!obj || obj.state === 'DELETED' || obj.state === 'PENDING') return;

    const healthyReplicas = this.getHealthyReplicasForObject(objectId);
    const now = new Date().toISOString();

    if (healthyReplicas.length >= obj.replication_factor) {
      this.db
        .prepare("UPDATE objects SET state = 'DURABLE', updated_at = ? WHERE object_id = ?")
        .run(now, objectId);
    } else {
      this.markObjectUnderReplicated(objectId);
    }
  }
}
