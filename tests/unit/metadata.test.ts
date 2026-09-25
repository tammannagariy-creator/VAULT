/**
 * tests/unit/metadata.test.ts
 *
 * Unit tests for the MetadataService.
 * Uses an in-memory SQLite database (`:memory:`) for speed.
 */

import { createDatabase, VaultDatabase } from '../../src/metadata/db';
import { MetadataService } from '../../src/metadata/service';

describe('MetadataService', () => {
  let db: VaultDatabase;
  let svc: MetadataService;

  beforeEach(() => {
    db = createDatabase(':memory:');
    svc = new MetadataService(db);
  });

  afterEach(() => {
    db.close();
  });

  // ─── Nodes ──────────────────────────────────────────────────────────────────

  describe('Nodes', () => {
    test('registerNode creates a new node', () => {
      const node = svc.registerNode({
        node_id: 'n1', address: 'localhost', port: 8081,
        storage_used: 0, storage_total: 0,
      });
      expect(node.node_id).toBe('n1');
      expect(node.state).toBe('HEALTHY');
    });

    test('re-registering existing node marks it RECOVERING', () => {
      svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      const node = svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      expect(node.state).toBe('RECOVERING');
    });

    test('updateNodeState transitions correctly', () => {
      svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      svc.updateNodeState('n1', 'FAILED');
      expect(svc.getNode('n1')?.state).toBe('FAILED');
    });

    test('getHealthyNodes excludes FAILED nodes', () => {
      svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      svc.registerNode({ node_id: 'n2', address: 'localhost', port: 8082, storage_used: 0, storage_total: 0 });
      svc.updateNodeState('n2', 'FAILED');
      const healthy = svc.getHealthyNodes();
      expect(healthy).toHaveLength(1);
      expect(healthy[0].node_id).toBe('n1');
    });
  });

  // ─── Objects ─────────────────────────────────────────────────────────────────

  describe('Objects', () => {
    test('createObject creates with PENDING state', () => {
      const obj = svc.createObject({
        logicalKey: 'test.txt',
        size: 100,
        checksum: 'sha256:abc',
        replicationFactor: 3,
      });
      expect(obj.logical_key).toBe('test.txt');
      expect(obj.version).toBe(1);
      expect(obj.state).toBe('PENDING');
    });

    test('getObjectByKey returns null for non-existent key', () => {
      expect(svc.getObjectByKey('missing')).toBeNull();
    });

    test('commitObject transitions to DURABLE', () => {
      const obj = svc.createObject({ logicalKey: 'f.txt', size: 1, checksum: 'sha256:a', replicationFactor: 3 });
      svc.commitObject(obj.object_id);
      expect(svc.getObjectById(obj.object_id)?.state).toBe('DURABLE');
    });

    test('updateObject increments version', () => {
      const obj = svc.createObject({ logicalKey: 'v.txt', size: 1, checksum: 'sha256:a', replicationFactor: 3 });
      svc.commitObject(obj.object_id);
      const updated = svc.updateObject(obj.object_id, { size: 2, checksum: 'sha256:b' });
      expect(updated.version).toBe(2);
    });

    test('deleteObject hides it from getObjectByKey', () => {
      const obj = svc.createObject({ logicalKey: 'd.txt', size: 1, checksum: 'sha256:a', replicationFactor: 3 });
      svc.commitObject(obj.object_id);
      svc.deleteObject(obj.object_id);
      expect(svc.getObjectByKey('d.txt')).toBeNull();
    });
  });

  // ─── Replicas ─────────────────────────────────────────────────────────────────

  describe('Replicas', () => {
    let objectId: string;

    beforeEach(() => {
      svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      const obj = svc.createObject({ logicalKey: 'r.txt', size: 10, checksum: 'sha256:abc', replicationFactor: 3 });
      objectId = obj.object_id;
    });

    test('addReplica creates a HEALTHY replica', () => {
      svc.addReplica({ objectId, nodeId: 'n1', version: 1, checksum: 'sha256:abc', size: 10 });
      const replicas = svc.getReplicasForObject(objectId);
      expect(replicas).toHaveLength(1);
      expect(replicas[0].state).toBe('HEALTHY');
    });

    test('addReplica is idempotent (upsert)', () => {
      svc.addReplica({ objectId, nodeId: 'n1', version: 1, checksum: 'sha256:abc', size: 10 });
      svc.addReplica({ objectId, nodeId: 'n1', version: 1, checksum: 'sha256:abc', size: 10 });
      expect(svc.getReplicasForObject(objectId)).toHaveLength(1);
    });

    test('updateReplicaState marks CORRUPT', () => {
      svc.addReplica({ objectId, nodeId: 'n1', version: 1, checksum: 'sha256:abc', size: 10 });
      const replica = svc.getReplicasForObject(objectId)[0];
      svc.updateReplicaState(replica.replica_id, 'CORRUPT');
      const updated = svc.getReplicasForObject(objectId)[0];
      expect(updated.state).toBe('CORRUPT');
    });

    test('markNodeReplicasMissing marks HEALTHY replicas as MISSING', () => {
      svc.addReplica({ objectId, nodeId: 'n1', version: 1, checksum: 'sha256:abc', size: 10 });
      svc.markNodeReplicasMissing('n1');
      const replicas = svc.getReplicasForObject(objectId);
      expect(replicas[0].state).toBe('MISSING');
    });
  });

  // ─── Repair Jobs ──────────────────────────────────────────────────────────────

  describe('Repair Jobs', () => {
    let objectId: string;

    beforeEach(() => {
      svc.registerNode({ node_id: 'n1', address: 'localhost', port: 8081, storage_used: 0, storage_total: 0 });
      svc.registerNode({ node_id: 'n2', address: 'localhost', port: 8082, storage_used: 0, storage_total: 0 });
      const obj = svc.createObject({ logicalKey: 'rep.txt', size: 10, checksum: 'sha256:abc', replicationFactor: 3 });
      objectId = obj.object_id;
    });

    test('createRepairJob creates a PENDING job', () => {
      const job = svc.createRepairJob({
        objectId,
        replicaId: null,
        targetNodeId: 'n2',
        sourceNodeId: 'n1',
        reason: 'MISSING',
      });
      expect(job.state).toBe('PENDING');
      expect(job.reason).toBe('MISSING');
    });

    test('duplicate repair job is deduplicated', () => {
      svc.createRepairJob({ objectId, replicaId: null, targetNodeId: 'n2', sourceNodeId: 'n1', reason: 'MISSING' });
      svc.createRepairJob({ objectId, replicaId: null, targetNodeId: 'n2', sourceNodeId: 'n1', reason: 'MISSING' });
      const jobs = svc.getPendingRepairJobs();
      expect(jobs).toHaveLength(1);
    });

    test('updateRepairJobState transitions to DONE', () => {
      const job = svc.createRepairJob({ objectId, replicaId: null, targetNodeId: 'n2', sourceNodeId: 'n1', reason: 'CORRUPT' });
      svc.updateRepairJobState(job.job_id, 'DONE');
      const jobs = svc.getPendingRepairJobs();
      expect(jobs).toHaveLength(0);
    });
  });

  // ─── Events ───────────────────────────────────────────────────────────────────

  describe('Events', () => {
    test('appendEvent stores an event', () => {
      svc.appendEvent('TEST_EVENT', 'something happened', { key: 'value' });
      const events = svc.getRecentEvents(10);
      expect(events.length).toBeGreaterThan(0);
      expect(events[0].type).toBe('TEST_EVENT');
    });
  });
});
