/**
 * tests/unit/placement.test.ts
 *
 * Unit tests for the PlacementService.
 */

import { PlacementService } from '../../src/gateway/placement';
import type { StorageNode } from '../../src/common/types';

function makeNode(id: string, storageUsed: number, state: 'HEALTHY' | 'FAILED' = 'HEALTHY'): StorageNode {
  return {
    node_id: id,
    address: 'localhost',
    port: 8080,
    state,
    last_heartbeat: new Date().toISOString(),
    storage_used: storageUsed,
    storage_total: 100_000,
    registered_at: new Date().toISOString(),
  };
}

describe('PlacementService', () => {
  const svc = new PlacementService();

  test('selectNodes returns requested count of nodes', () => {
    const nodes = [makeNode('n1', 10), makeNode('n2', 20), makeNode('n3', 30)];
    const selected = svc.selectNodes(nodes, 2);
    expect(selected).toHaveLength(2);
  });

  test('selectNodes prefers least-used nodes first', () => {
    const nodes = [makeNode('n1', 100), makeNode('n2', 10), makeNode('n3', 50)];
    const selected = svc.selectNodes(nodes, 1);
    expect(selected[0].node_id).toBe('n2'); // least used
  });

  test('selectNodes excludes specified nodes', () => {
    const nodes = [makeNode('n1', 10), makeNode('n2', 20), makeNode('n3', 30)];
    const selected = svc.selectNodes(nodes, 2, ['n1']);
    expect(selected.map(n => n.node_id)).not.toContain('n1');
  });

  test('selectNodes returns all available if fewer than requested', () => {
    const nodes = [makeNode('n1', 10)];
    const selected = svc.selectNodes(nodes, 3);
    expect(selected).toHaveLength(1);
  });

  test('selectRepairTarget returns one node not in excludeList', () => {
    const nodes = [makeNode('n1', 10), makeNode('n2', 20), makeNode('n3', 30)];
    const target = svc.selectRepairTarget(nodes, ['n1', 'n2']);
    expect(target?.node_id).toBe('n3');
  });

  test('selectRepairTarget returns null if all nodes excluded', () => {
    const nodes = [makeNode('n1', 10)];
    const target = svc.selectRepairTarget(nodes, ['n1']);
    expect(target).toBeNull();
  });

  test('selectRepairSource picks least loaded', () => {
    const nodes = [makeNode('n1', 50), makeNode('n2', 10), makeNode('n3', 80)];
    const source = svc.selectRepairSource(nodes);
    expect(source?.node_id).toBe('n2');
  });

  test('selectRepairSource returns null for empty list', () => {
    expect(svc.selectRepairSource([])).toBeNull();
  });
});
