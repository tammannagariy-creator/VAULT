/**
 * storage/index.ts
 *
 * Storage Node — Express HTTP server.
 *
 * A storage node is intentionally simple. It does three things:
 *   1. Store raw bytes to disk (PUT /store/:objectId)
 *   2. Return raw bytes from disk (GET /store/:objectId)
 *   3. Delete bytes from disk (DELETE /store/:objectId)
 *   4. Report its health (GET /health)
 *
 * It does NOT make decisions about replication, quorum, or metadata.
 * All that logic lives in the gateway's Coordinator.
 *
 * The storage node sends periodic heartbeats to the gateway so the
 * FailureDetector can track its health.
 *
 * Environment variables:
 *   NODE_ID         — unique identifier (e.g., "node-1")
 *   NODE_PORT       — port to listen on (e.g., 8081)
 *   NODE_ADDRESS    — address to advertise to the gateway (e.g., "localhost")
 *   STORAGE_PATH    — directory to store object files
 *   GATEWAY_ADDRESS — gateway host
 *   GATEWAY_PORT    — gateway port
 *   HEARTBEAT_INTERVAL — ms between heartbeats (default 5000)
 *   SCAN_INTERVAL   — ms between integrity scans (default 60000)
 */

import express from 'express';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { loadConfig } from '../common/config.js';
import { ObjectStore } from './store.js';
import { computeChecksum, verifyChecksum } from './checksum.js';
import { IntegrityScanner } from './scanner.js';

const config = loadConfig();
const app = express();

// Parse raw binary bodies for object PUT requests
app.use('/store', express.raw({ type: '*/*', limit: '500mb' }));
app.use(express.json());

const store = new ObjectStore(config.storageBasePath);
const scanner = new IntegrityScanner(
  {
    nodeId: config.nodeId,
    storageBasePath: config.storageBasePath,
    gatewayAddress: config.gatewayAddress,
    gatewayPort: config.gatewayPort,
    scanInterval: config.scanInterval,
  },
  store
);

// ─── Health Check ─────────────────────────────────────────────────────────────

app.get('/health', (_req, res) => {
  res.json({
    node_id: config.nodeId,
    status: 'HEALTHY',
    storage_used: store.getStorageUsed(),
    uptime: process.uptime(),
  });
});

// ─── Store Object (Internal: Gateway → Node) ──────────────────────────────────

/**
 * PUT /store/:objectId
 *
 * Store raw object bytes.
 * The gateway sends:
 *   - X-Object-Version: version number
 *   - X-Object-Checksum: expected checksum "sha256:<hex>"
 *   - Body: raw bytes
 *
 * The node:
 *   1. Receives the bytes
 *   2. Computes the checksum and verifies it matches the header
 *   3. Writes atomically to disk
 *   4. Writes a sidecar .meta file for the scanner
 *   5. Returns 200 with the stored checksum
 */
app.put('/store/:objectId', (req, res) => {
  const { objectId } = req.params;
  const expectedChecksum = req.headers['x-object-checksum'] as string;
  const version = parseInt(req.headers['x-object-version'] as string ?? '1', 10);

  if (!expectedChecksum) {
    res.status(400).json({ error: 'Missing X-Object-Checksum header' });
    return;
  }

  const data = req.body as Buffer;

  if (!Buffer.isBuffer(data) || data.length === 0) {
    res.status(400).json({ error: 'Empty or invalid body' });
    return;
  }

  // Verify the checksum before writing to disk
  // This catches data corruption in transit (gateway → node)
  if (!verifyChecksum(data, expectedChecksum)) {
    const actual = computeChecksum(data);
    console.error(`[Node ${config.nodeId}] Checksum mismatch during write — expected ${expectedChecksum}, got ${actual}`);
    res.status(422).json({
      error: 'Checksum mismatch',
      expected: expectedChecksum,
      actual,
    });
    return;
  }

  try {
    store.write(objectId, data);

    // Write sidecar for integrity scanner
    IntegrityScanner.writeSidecar(config.storageBasePath, objectId, {
      checksum: expectedChecksum,
      object_id: objectId,
      version,
    });

    console.log(`[Node ${config.nodeId}] Stored object ${objectId} (${data.length} bytes, v${version})`);

    res.json({
      object_id: objectId,
      node_id: config.nodeId,
      checksum: expectedChecksum,
      size: data.length,
      version,
    });
  } catch (err) {
    console.error(`[Node ${config.nodeId}] Write failed for object ${objectId}:`, err);
    res.status(500).json({ error: 'Write failed' });
  }
});

// ─── Retrieve Object (Internal: Gateway → Node) ───────────────────────────────

/**
 * GET /store/:objectId
 *
 * Return raw object bytes.
 * Responds with:
 *   - X-Object-Checksum: stored checksum
 *   - X-Object-Version: stored version
 *   - Body: raw bytes
 *
 * The Coordinator verifies the checksum after receiving the response.
 */
app.get('/store/:objectId', (req, res) => {
  const { objectId } = req.params;

  const data = store.read(objectId);
  if (!data) {
    res.status(404).json({ error: 'Object not found', object_id: objectId });
    return;
  }

  // Read sidecar to get stored checksum and version
  const sidecarPath = path.join(config.storageBasePath, `${objectId}.meta`);
  let storedChecksum = '';
  let storedVersion = 0;
  try {
    const sidecar = JSON.parse(fs.readFileSync(sidecarPath, 'utf-8')) as { checksum: string; version: number };
    storedChecksum = sidecar.checksum;
    storedVersion = sidecar.version;
  } catch {
    // No sidecar — compute checksum on the fly
    storedChecksum = computeChecksum(data);
  }

  res.set('X-Object-Checksum', storedChecksum);
  res.set('X-Object-Version', String(storedVersion));
  res.set('Content-Type', 'application/octet-stream');
  res.send(data);
});

// ─── Delete Object (Internal: Gateway → Node) ─────────────────────────────────

/**
 * DELETE /store/:objectId
 *
 * Remove the object file and its sidecar from disk.
 */
app.delete('/store/:objectId', (req, res) => {
  const { objectId } = req.params;
  const deleted = store.delete(objectId);

  // Also remove the sidecar
  try {
    fs.unlinkSync(path.join(config.storageBasePath, `${objectId}.meta`));
  } catch { /* sidecar may not exist */ }

  if (deleted) {
    console.log(`[Node ${config.nodeId}] Deleted object ${objectId}`);
    res.json({ object_id: objectId, deleted: true });
  } else {
    res.status(404).json({ error: 'Object not found', object_id: objectId });
  }
});

// ─── List stored objects (for repair/rebalance) ───────────────────────────────

app.get('/store', (_req, res) => {
  const objectIds = store.listObjectIds();
  res.json({ node_id: config.nodeId, objects: objectIds, count: objectIds.length });
});

// ─── Fault injection endpoint (demo tool) ─────────────────────────────────────

/**
 * POST /admin/corrupt/:objectId
 *
 * For hackathon demo: overwrite a stored file with garbage bytes.
 * The integrity scanner will detect the mismatch and trigger repair.
 */
app.post('/admin/corrupt/:objectId', (req, res) => {
  const { objectId } = req.params;

  if (!store.exists(objectId)) {
    res.status(404).json({ error: 'Object not found on this node' });
    return;
  }

  try {
    // Write random bytes to corrupt the file
    const corrupt = crypto.randomBytes(64);
    store.write(objectId, corrupt);

    console.warn(`[Node ${config.nodeId}] CORRUPTION INJECTED for object ${objectId} (demo)`);
    res.json({ corrupted: true, object_id: objectId, node_id: config.nodeId });
  } catch (err) {
    res.status(500).json({ error: 'Failed to inject corruption' });
  }
});

// ─── Heartbeat registration ───────────────────────────────────────────────────

async function registerWithGateway(): Promise<void> {
  const gatewayUrl = `http://${config.gatewayAddress}:${config.gatewayPort}`;
  const payload = {
    node_id: config.nodeId,
    address: config.nodeAddress,
    port: config.nodePort,
    storage_used: store.getStorageUsed(),
    storage_total: 0,
  };

  let attempts = 0;
  while (attempts < 20) {
    try {
      await axios.post(`${gatewayUrl}/internal/nodes/register`, payload, { timeout: 5000 });
      console.log(`[Node ${config.nodeId}] Registered with gateway at ${gatewayUrl}`);
      return;
    } catch {
      attempts++;
      console.log(`[Node ${config.nodeId}] Gateway not ready, retrying... (${attempts}/20)`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }
  console.error(`[Node ${config.nodeId}] Failed to register with gateway after 20 attempts`);
}

function startHeartbeat(): void {
  setInterval(async () => {
    try {
      await axios.post(
        `http://${config.gatewayAddress}:${config.gatewayPort}/internal/nodes/heartbeat`,
        {
          node_id: config.nodeId,
          storage_used: store.getStorageUsed(),
          storage_total: 0,
        },
        { timeout: 5000 }
      );
    } catch {
      // Heartbeat failure is expected if gateway is temporarily unreachable
      // The gateway-side failure detector handles the timeout logic
    }
  }, config.heartbeatInterval);
}

// ─── Server Startup ───────────────────────────────────────────────────────────

app.listen(config.nodePort, () => {
  console.log(`[Node ${config.nodeId}] Storage node listening on port ${config.nodePort}`);
  console.log(`[Node ${config.nodeId}] Storage path: ${config.storageBasePath}`);

  // Register with gateway and start sending heartbeats
  registerWithGateway().then(() => {
    startHeartbeat();
    scanner.start();
  });
});

process.on('SIGTERM', () => {
  console.log(`[Node ${config.nodeId}] Received SIGTERM, shutting down gracefully`);
  scanner.stop();
  process.exit(0);
});
