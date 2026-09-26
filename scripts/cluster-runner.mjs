#!/usr/bin/env node
/**
 * scripts/cluster-runner.mjs
 *
 * Universal Production Cluster Runner for Cloud & Container Deployments.
 * Boots and supervises all components in a single container or server environment:
 *   - Gateway (Public API + Control Plane on PORT / 8080)
 *   - Node-1  (Internal Storage Node on 8081)
 *   - Node-2  (Internal Storage Node on 8082)
 *   - Node-3  (Internal Storage Node on 8083)
 *
 * Compatible with Render, Railway, Fly.io, Cloud Run, AWS App Runner, and Docker.
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import http from 'http';

const ROOT_DIR = process.cwd();
const DATA_DIR = process.env.DATA_DIR || (fs.existsSync('/data') ? '/data' : path.join(ROOT_DIR, 'data'));
const GATEWAY_PORT = process.env.PORT || process.env.GATEWAY_PORT || '8080';
const NODE_1_PORT = process.env.NODE_1_PORT || '8081';
const NODE_2_PORT = process.env.NODE_2_PORT || '8082';
const NODE_3_PORT = process.env.NODE_3_PORT || '8083';

console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║       VAULT DISTRIBUTED OBJECT STORAGE — CLUSTER RUNNER        ║');
console.log('╚════════════════════════════════════════════════════════════════╝');
console.log(`[INIT] Root Directory : ${ROOT_DIR}`);
console.log(`[INIT] Data Directory : ${DATA_DIR}`);
console.log(`[INIT] Gateway Port   : ${GATEWAY_PORT} (Public Endpoint)`);
console.log(`[INIT] Storage Nodes  : ${NODE_1_PORT}, ${NODE_2_PORT}, ${NODE_3_PORT}`);

// Ensure required data directories exist
const dirsToCreate = [
  DATA_DIR,
  path.join(DATA_DIR, 'gateway'),
  path.join(DATA_DIR, 'node-1'),
  path.join(DATA_DIR, 'node-2'),
  path.join(DATA_DIR, 'node-3'),
];

for (const dir of dirsToCreate) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

const processes = [];

function startProcess(name, scriptPath, envVars) {
  const env = {
    ...process.env,
    ...envVars,
  };

  const isDist = fs.existsSync(path.join(ROOT_DIR, 'dist'));
  const cmd = isDist ? 'node' : 'npx';
  const args = isDist ? [scriptPath.replace('src/', 'dist/').replace('.ts', '.js')] : ['tsx', scriptPath];

  console.log(`[SPAWN] Starting ${name} (${cmd} ${args.join(' ')})`);

  const child = spawn(cmd, args, {
    cwd: ROOT_DIR,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: process.platform === 'win32',
  });

  child.stdout.on('data', (chunk) => {
    const lines = chunk.toString().trim().split('\n');
    for (const line of lines) {
      if (line.trim()) console.log(`[${name}] ${line.trim()}`);
    }
  });

  child.stderr.on('data', (chunk) => {
    const lines = chunk.toString().trim().split('\n');
    for (const line of lines) {
      if (line.trim()) console.error(`[${name}:ERR] ${line.trim()}`);
    }
  });

  child.on('exit', (code, signal) => {
    console.warn(`[EXIT] ${name} exited with code ${code} (signal: ${signal})`);
  });

  processes.push({ name, child });
  return child;
}

// 1. Start Vault Gateway
const gatewayEnv = {
  PORT: GATEWAY_PORT,
  GATEWAY_PORT: GATEWAY_PORT,
  REPLICATION_FACTOR: '3',
  WRITE_QUORUM: '2',
  READ_QUORUM: '2',
  HEARTBEAT_INTERVAL: '5000',
  HEARTBEAT_TIMEOUT: '15000',
  REPAIR_INTERVAL: '10000',
  SCAN_INTERVAL: '60000',
  METADATA_DATABASE: path.join(DATA_DIR, 'gateway', 'vault.db'),
};

startProcess('GATEWAY', 'src/gateway/index.ts', gatewayEnv);

// Wait for Gateway to initialize before launching storage nodes
async function waitForGateway(maxRetries = 20) {
  for (let i = 0; i < maxRetries; i++) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    try {
      const isUp = await new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${GATEWAY_PORT}/health`, (res) => {
          resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1000, () => {
          req.destroy();
          resolve(false);
        });
      });
      if (isUp) {
        console.log(`[GATEWAY:READY] Gateway health check passed on port ${GATEWAY_PORT}`);
        return true;
      }
    } catch {
      // Retry
    }
  }
  console.warn('[GATEWAY:WARN] Gateway took longer than expected to respond, proceeding with storage nodes...');
  return false;
}

async function bootCluster() {
  await waitForGateway();

  // 2. Start Storage Node 1
  startProcess('NODE-1', 'src/storage/index.ts', {
    NODE_ID: 'node-1',
    NODE_PORT: NODE_1_PORT,
    NODE_ADDRESS: 'localhost',
    STORAGE_PATH: path.join(DATA_DIR, 'node-1'),
    GATEWAY_ADDRESS: 'localhost',
    GATEWAY_PORT: GATEWAY_PORT,
    HEARTBEAT_INTERVAL: '5000',
    HEARTBEAT_TIMEOUT: '15000',
    SCAN_INTERVAL: '60000',
  });

  // 3. Start Storage Node 2
  startProcess('NODE-2', 'src/storage/index.ts', {
    NODE_ID: 'node-2',
    NODE_PORT: NODE_2_PORT,
    NODE_ADDRESS: 'localhost',
    STORAGE_PATH: path.join(DATA_DIR, 'node-2'),
    GATEWAY_ADDRESS: 'localhost',
    GATEWAY_PORT: GATEWAY_PORT,
    HEARTBEAT_INTERVAL: '5000',
    HEARTBEAT_TIMEOUT: '15000',
    SCAN_INTERVAL: '60000',
  });

  // 4. Start Storage Node 3
  startProcess('NODE-3', 'src/storage/index.ts', {
    NODE_ID: 'node-3',
    NODE_PORT: NODE_3_PORT,
    NODE_ADDRESS: 'localhost',
    STORAGE_PATH: path.join(DATA_DIR, 'node-3'),
    GATEWAY_ADDRESS: 'localhost',
    GATEWAY_PORT: GATEWAY_PORT,
    HEARTBEAT_INTERVAL: '5000',
    HEARTBEAT_TIMEOUT: '15000',
    SCAN_INTERVAL: '60000',
  });

  console.log('────────────────────────────────────────────────────────────────');
  console.log('  Vault Cluster Fully Operational.');
  console.log(`  Live Control Plane: http://0.0.0.0:${GATEWAY_PORT}/ui/`);
  console.log('────────────────────────────────────────────────────────────────');
}

bootCluster();

function shutdown(signal) {
  console.log(`\n[SHUTDOWN] Received ${signal}. Terminating all cluster processes...`);
  for (const { name, child } of processes) {
    try {
      console.log(`[SHUTDOWN] Stopping ${name}...`);
      child.kill('SIGTERM');
    } catch (err) {
      console.error(`[SHUTDOWN:ERR] Failed to kill ${name}:`, err.message);
    }
  }
  setTimeout(() => {
    console.log('[SHUTDOWN] Exit complete.');
    process.exit(0);
  }, 1000);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
