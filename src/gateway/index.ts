/**
 * gateway/index.ts
 *
 * Vault Gateway — the main entry point for the distributed storage system.
 *
 * This process runs:
 *   - HTTP server (client-facing API on GATEWAY_PORT)
 *   - MetadataService (SQLite — single source of truth)
 *   - Coordinator (quorum reads/writes)
 *   - PlacementService (node selection)
 *   - FailureDetector (heartbeat tracking)
 *   - RepairWorker (background replica repair)
 *   - Rebalancer (node join/drain)
 *
 * The storage nodes run as separate processes (src/storage/index.ts).
 * They communicate with this gateway via HTTP.
 *
 * Architecture summary:
 *   CLIENT → Gateway (this process) → Storage Nodes (separate processes)
 *            ↑
 *       SQLite metadata
 */

import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { loadConfig } from '../common/config.js';
import { createDatabase } from '../metadata/db.js';
import { MetadataService } from '../metadata/service.js';
import { Coordinator } from './coordinator.js';
import { PlacementService } from './placement.js';
import { FailureDetector } from '../membership/detector.js';
import { RepairWorker } from '../repair/worker.js';
import { Rebalancer } from '../rebalancer/rebalancer.js';
import { objectsRouter } from './routes/objects.js';
import { nodesRouter } from './routes/nodes.js';
import { clusterRouter } from './routes/cluster.js';
import { repairsRouter } from './routes/repairs.js';

const config = loadConfig();
(global as any).__vaultConfig = config;

// ─── Database & Services ──────────────────────────────────────────────────────

const db = createDatabase(config.metadataDatabase);
const metadata = new MetadataService(db);
const coordinator = new Coordinator();
const placement = new PlacementService();
const repairWorker = new RepairWorker(metadata, coordinator, placement, {
  repairInterval: config.repairInterval,
});
const rebalancer = new Rebalancer(metadata, placement);
const failureDetector = new FailureDetector(metadata, {
  heartbeatTimeout: config.heartbeatTimeout,
  checkInterval: Math.min(config.heartbeatTimeout / 3, 5000),
});

// Wire failure detection → repair worker
failureDetector.onFailure((nodeId) => {
  console.log(`[Gateway] Node ${nodeId} failed — scheduling repairs`);
  repairWorker.scheduleRepairsForFailedNode(nodeId);
});

// ─── Express App ──────────────────────────────────────────────────────────────

const app = express();

// CORS for dashboard
app.use(cors({
  exposedHeaders: ['X-Object-Id', 'X-Object-Version', 'X-Object-Checksum', 'X-Vault-Checksum', 'X-Vault-Version', 'ETag']
}));

// Parse raw binary for object uploads
app.use('/objects', express.raw({ type: '*/*', limit: '500mb' }));

// Parse JSON for everything else
app.use(express.json());

// ─── Routes ───────────────────────────────────────────────────────────────────

// Object CRUD
app.use('/objects', objectsRouter(metadata, coordinator, placement, config));

// Node management + internal endpoints
const nodes = nodesRouter(metadata, rebalancer, repairWorker);
app.use(nodes);

// Cluster status & events
const cluster = clusterRouter(metadata);
app.use('/cluster', cluster);
app.use('/health', cluster); // /health is a convenience alias

// Repair jobs
app.use('/repairs', repairsRouter(metadata, repairWorker));

// ─── Dashboard UI Static Files ───────────────────────────────────────────────
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.resolve(__dirname, '../../dashboard/public');
app.use('/ui', express.static(publicDir));
app.use('/dashboard', express.static(publicDir));

// ─── Fault injection endpoint (demo tool) ─────────────────────────────────────

/**
 * POST /admin/corrupt/:nodeId/:objectId
 *
 * For hackathon demo: inject corruption into a specific replica.
 * This asks the storage node to overwrite a file with garbage bytes.
 * The integrity scanner will then detect the mismatch.
 */
app.post('/admin/corrupt/:nodeId/:objectId', async (req, res) => {
  const { nodeId, objectId } = req.params;
  const node = metadata.getNode(nodeId);
  const obj = metadata.getObjectById(objectId);

  if (!node || !obj) {
    res.status(404).json({ error: 'Node or object not found' });
    return;
  }

  try {
    // Ask the storage node to corrupt the file
    const axios = await import('axios');
    await axios.default.post(
      `http://${node.address}:${node.port}/admin/corrupt/${objectId}`,
      {},
      { timeout: 5000 }
    );

    metadata.appendEvent(
      'CORRUPTION_INJECTED',
      `Corruption injected on node ${nodeId} for object ${objectId} (demo)`,
      { node_id: nodeId, object_id: objectId }
    );

    res.json({ injected: true, node_id: nodeId, object_id: objectId });
  } catch (err) {
    res.status(500).json({ error: 'Failed to inject corruption', detail: String(err) });
  }
});

// Root — redirect to status
app.get('/', (_req, res) => {
  res.json({
    service: 'Vault Gateway',
    version: '1.0.0',
    docs: 'https://github.com/vault-distributed-storage',
    endpoints: {
      objects: '/objects/:key',
      nodes: '/nodes',
      cluster: '/cluster/status',
      health: '/health',
      repairs: '/repairs',
      events: '/cluster/events',
      events_stream: '/cluster/events/stream',
      ui: '/ui',
      dashboard: '/dashboard',
    },
  });
});

// ─── Start ────────────────────────────────────────────────────────────────────

const server = app.listen(config.gatewayPort, () => {
  console.log('');
  console.log('╔══════════════════════════════════════════════╗');
  console.log('║          VAULT GATEWAY — STARTED             ║');
  console.log('╚══════════════════════════════════════════════╝');
  console.log(`  Port:               ${config.gatewayPort}`);
  console.log(`  Replication Factor: N=${config.replicationFactor}`);
  console.log(`  Write Quorum:       W=${config.writeQuorum}`);
  console.log(`  Read Quorum:        R=${config.readQuorum}`);
  console.log(`  Metadata DB:        ${config.metadataDatabase}`);
  console.log(`  Heartbeat Timeout:  ${config.heartbeatTimeout}ms`);
  console.log(`  Repair Interval:    ${config.repairInterval}ms`);
  console.log('');

  // Start background services
  failureDetector.start();
  repairWorker.start();

  metadata.appendEvent('GATEWAY_STARTED', 'Vault gateway started', {
    port: config.gatewayPort,
    n: config.replicationFactor,
    w: config.writeQuorum,
    r: config.readQuorum,
  });
});

process.on('SIGTERM', () => {
  console.log('[Gateway] Received SIGTERM, shutting down');
  failureDetector.stop();
  repairWorker.stop();
  server.close(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('[Gateway] Received SIGINT, shutting down');
  failureDetector.stop();
  repairWorker.stop();
  server.close(() => process.exit(0));
});
