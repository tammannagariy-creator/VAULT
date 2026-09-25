/**
 * gateway/coordinator.ts
 *
 * Coordinator — implements quorum-based reads and writes.
 *
 * PUT flow (write quorum W):
 *   1. Send the object to all N chosen nodes in parallel.
 *   2. Wait for W acknowledgements.
 *   3. If W acks received → success → commit metadata.
 *   4. If fewer than W acks → failure → rollback (don't commit metadata).
 *   5. Nodes that didn't ack still have the data (they write it). This
 *      is acceptable because the next repair cycle will clean them up
 *      via the stale-replica detection.
 *
 * GET flow (read quorum R):
 *   1. Query R replicas in parallel.
 *   2. Verify checksum on each response.
 *   3. Return the first valid response to the client.
 *   4. If a response has a bad checksum → mark that replica CORRUPT → trigger repair.
 *   5. If fewer than R valid responses → failure → 503.
 *
 * Consistency guarantee:
 *   With R=2, W=2, N=3 → R + W > N (2 + 2 > 3).
 *   Every read quorum overlaps with every write quorum by at least 1 node.
 *   This means reads always see the latest committed write.
 */

import axios from 'axios';
import { nodeUrl } from '../common/config.js';
import { verifyChecksum } from '../storage/checksum.js';
import type { StorageNode, ReplicaMetadata, QuorumWriteResult, QuorumReadResult } from '../common/types.js';

// Timeout for individual node requests (ms)
const NODE_REQUEST_TIMEOUT = 10_000;

export class Coordinator {
  /**
   * Write an object to multiple nodes in parallel and wait for quorum.
   *
   * @returns QuorumWriteResult with success flag and which nodes acked
   */
  async writeQuorum(
    objectId: string,
    version: number,
    checksum: string,
    data: Buffer,
    targetNodes: StorageNode[],
    writeQuorum: number
  ): Promise<QuorumWriteResult> {
    const results = await Promise.allSettled(
      targetNodes.map(node => this.writeToNode(node, objectId, version, checksum, data))
    );

    const successes: string[] = [];
    const failures: string[] = [];

    results.forEach((result, i) => {
      if (result.status === 'fulfilled') {
        successes.push(targetNodes[i].node_id);
      } else {
        failures.push(targetNodes[i].node_id);
        console.error(
          `[Coordinator] Write to node ${targetNodes[i].node_id} failed:`,
          result.reason?.message ?? result.reason
        );
      }
    });

    const success = successes.length >= writeQuorum;

    if (success) {
      console.log(
        `[Coordinator] PUT ${objectId} — quorum achieved (${successes.length}/${targetNodes.length} nodes)`
      );
    } else {
      console.warn(
        `[Coordinator] PUT ${objectId} — quorum FAILED (${successes.length}/${writeQuorum} required)`
      );
    }

    return { success, ackCount: successes.length, failures };
  }

  /**
   * Read an object from multiple replicas in parallel and return the first
   * valid (checksum-verified) response.
   */
  async readQuorum(
    objectId: string,
    expectedChecksum: string,
    replicas: ReplicaMetadata[],
    readableNodes: StorageNode[],
    readQuorum: number
  ): Promise<QuorumReadResult> {
    // Map replica → node for each healthy replica
    const nodeMap = new Map(readableNodes.map(n => [n.node_id, n]));
    const replicasWithNodes = replicas
      .filter(r => r.state === 'HEALTHY' && nodeMap.has(r.node_id))
      .map(r => ({ replica: r, node: nodeMap.get(r.node_id)! }));

    if (replicasWithNodes.length === 0) {
      return { success: false, data: null, checksum: '', version: 0, sourceNodeId: '' };
    }

    // Read from all available replicas in parallel
    const results = await Promise.allSettled(
      replicasWithNodes.map(({ replica, node }) =>
        this.readFromNode(node, objectId, expectedChecksum, replica)
      )
    );

    const corruptNodeIds: string[] = [];
    let validResult: QuorumReadResult | null = null;
    let validCount = 0;

    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      if (result.status === 'fulfilled' && result.value.success) {
        validCount++;
        if (!validResult) {
          validResult = result.value;
        }
      } else if (result.status === 'fulfilled' && result.value.corrupt) {
        corruptNodeIds.push(replicasWithNodes[i].node.node_id);
      }
    }

    return validResult && validCount >= readQuorum
      ? validResult
      : { success: false, data: null, checksum: '', version: 0, sourceNodeId: '' };
  }

  /**
   * Delete an object from all its replicas.
   * Returns list of nodes that successfully deleted.
   */
  async deleteFromNodes(
    objectId: string,
    replicas: ReplicaMetadata[],
    nodeMap: Map<string, StorageNode>
  ): Promise<string[]> {
    const deletedNodes: string[] = [];

    await Promise.allSettled(
      replicas.map(async (replica) => {
        const node = nodeMap.get(replica.node_id);
        if (!node || node.state === 'FAILED') return;

        try {
          await axios.delete(
            `${nodeUrl(node.address, node.port)}/store/${objectId}`,
            { timeout: NODE_REQUEST_TIMEOUT }
          );
          deletedNodes.push(node.node_id);
        } catch (err) {
          console.warn(`[Coordinator] DELETE from node ${node.node_id} failed:`, err);
        }
      })
    );

    return deletedNodes;
  }

  /**
   * Copy an object from a source node to a target node.
   * Used by the repair worker during replica restoration.
   *
   * Returns true if the copy was successful and checksum-verified.
   */
  async copyReplica(
    objectId: string,
    version: number,
    expectedChecksum: string,
    sourceNode: StorageNode,
    targetNode: StorageNode
  ): Promise<boolean> {
    try {
      // 1. Fetch from source
      const response = await axios.get(
        `${nodeUrl(sourceNode.address, sourceNode.port)}/store/${objectId}`,
        { responseType: 'arraybuffer', timeout: NODE_REQUEST_TIMEOUT }
      );

      const data = Buffer.from(response.data as ArrayBuffer);
      const actualChecksum = response.headers['x-object-checksum'] as string;

      // 2. Verify checksum of source data
      if (!verifyChecksum(data, expectedChecksum)) {
        console.error(
          `[Coordinator] Source data from ${sourceNode.node_id} is corrupt for object ${objectId}`
        );
        return false;
      }

      // 3. Write to target
      await axios.put(
        `${nodeUrl(targetNode.address, targetNode.port)}/store/${objectId}`,
        data,
        {
          headers: {
            'Content-Type': 'application/octet-stream',
            'X-Object-Checksum': expectedChecksum || actualChecksum,
            'X-Object-Version': String(version),
          },
          timeout: NODE_REQUEST_TIMEOUT,
        }
      );

      return true;
    } catch (err) {
      console.error(
        `[Coordinator] copyReplica failed (${sourceNode.node_id} → ${targetNode.node_id}):`,
        err
      );
      return false;
    }
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  private async writeToNode(
    node: StorageNode,
    objectId: string,
    version: number,
    checksum: string,
    data: Buffer
  ): Promise<void> {
    await axios.put(
      `${nodeUrl(node.address, node.port)}/store/${objectId}`,
      data,
      {
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-Object-Checksum': checksum,
          'X-Object-Version': String(version),
        },
        timeout: NODE_REQUEST_TIMEOUT,
      }
    );
  }

  private async readFromNode(
    node: StorageNode,
    objectId: string,
    expectedChecksum: string,
    replica: ReplicaMetadata
  ): Promise<QuorumReadResult & { corrupt?: boolean }> {
    const response = await axios.get(
      `${nodeUrl(node.address, node.port)}/store/${objectId}`,
      { responseType: 'arraybuffer', timeout: NODE_REQUEST_TIMEOUT }
    );

    const data = Buffer.from(response.data as ArrayBuffer);
    const version = parseInt(response.headers['x-object-version'] as string ?? '0', 10);

    // Verify checksum — critical safety check (System Invariant SI-02)
    if (!verifyChecksum(data, expectedChecksum)) {
      const actual = verifyChecksum(data, expectedChecksum);
      console.warn(
        `[Coordinator] Checksum mismatch on replica ${replica.replica_id} on node ${node.node_id}`
      );
      return {
        success: false,
        data: null,
        checksum: expectedChecksum,
        version,
        sourceNodeId: node.node_id,
        corrupt: true,
      };
    }

    return {
      success: true,
      data,
      checksum: expectedChecksum,
      version,
      sourceNodeId: node.node_id,
    };
  }
}
