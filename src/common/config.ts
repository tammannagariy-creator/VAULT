/**
 * common/config.ts
 *
 * Loads Vault configuration from environment variables.
 * Provides sensible defaults for local development.
 *
 * Design Decision:
 *   We use environment variables (not a config file) because they work
 *   naturally with Docker Compose, are easy to override per-process,
 *   and require no extra parsing libraries.
 */

export interface VaultConfig {
  // Distributed storage settings
  replicationFactor: number;  // N — how many copies of each object
  writeQuorum: number;        // W — minimum acks needed for a PUT to succeed
  readQuorum: number;         // R — minimum reads needed to satisfy a GET

  // Timing (milliseconds)
  heartbeatInterval: number;  // how often storage nodes ping the gateway
  heartbeatTimeout: number;   // how long before a node is marked SUSPECTED/FAILED
  repairInterval: number;     // how often the repair worker runs
  scanInterval: number;       // how often the integrity scanner runs

  // Data integrity
  checksumAlgorithm: string;  // "sha256" (only supported value currently)

  // Storage
  storageBasePath: string;    // directory where this storage node writes files
  nodeId: string;             // unique identifier for this node
  nodePort: number;           // port this storage node listens on
  nodeAddress: string;        // address other nodes use to reach this node

  // Gateway
  gatewayPort: number;
  gatewayAddress: string;     // address storage nodes use to reach the gateway

  // Metadata
  metadataDatabase: string;   // path to the SQLite database file
}

export function loadConfig(): VaultConfig {
  const config: VaultConfig = {
    // Replication — R + W > N ensures consistency (2 + 2 > 3)
    replicationFactor: parseInt(process.env.REPLICATION_FACTOR ?? '3', 10),
    writeQuorum: parseInt(process.env.WRITE_QUORUM ?? '2', 10),
    readQuorum: parseInt(process.env.READ_QUORUM ?? '2', 10),

    // Timing
    heartbeatInterval: parseInt(process.env.HEARTBEAT_INTERVAL ?? '5000', 10),
    heartbeatTimeout: parseInt(process.env.HEARTBEAT_TIMEOUT ?? '15000', 10),
    repairInterval: parseInt(process.env.REPAIR_INTERVAL ?? '10000', 10),
    scanInterval: parseInt(process.env.SCAN_INTERVAL ?? '60000', 10),

    // Integrity
    checksumAlgorithm: process.env.CHECKSUM_ALGORITHM ?? 'sha256',

    // Storage node identity
    storageBasePath: process.env.STORAGE_PATH ?? './data',
    nodeId: process.env.NODE_ID ?? 'node-1',
    nodePort: parseInt(process.env.NODE_PORT ?? '8081', 10),
    nodeAddress: process.env.NODE_ADDRESS ?? 'localhost',

    // Gateway (supports dynamic cloud port assignment via PORT)
    gatewayPort: parseInt(process.env.PORT ?? process.env.GATEWAY_PORT ?? '8080', 10),
    gatewayAddress: process.env.GATEWAY_ADDRESS ?? 'localhost',

    // Metadata
    metadataDatabase: process.env.METADATA_DATABASE ?? './vault.db',
  };

  // Validate quorum invariants at startup
  validateQuorumConfig(config);

  return config;
}

/**
 * Validates that the quorum configuration is mathematically consistent.
 *
 * Key invariant: R + W > N
 * This guarantees that every read quorum and write quorum share at
 * least one node, preventing stale reads after successful writes.
 */
function validateQuorumConfig(config: VaultConfig): void {
  const { replicationFactor: N, writeQuorum: W, readQuorum: R } = config;

  if (W < 1 || R < 1) {
    throw new Error(`Invalid quorum config: W=${W}, R=${R} — both must be >= 1`);
  }

  if (W > N) {
    throw new Error(
      `Invalid quorum config: WRITE_QUORUM(${W}) > REPLICATION_FACTOR(${N})`
    );
  }

  if (R > N) {
    throw new Error(
      `Invalid quorum config: READ_QUORUM(${R}) > REPLICATION_FACTOR(${N})`
    );
  }

  if (R + W <= N) {
    console.warn(
      `[CONFIG] WARNING: R(${R}) + W(${W}) <= N(${N}). ` +
      `This allows stale reads. Consider increasing R or W for stronger consistency.`
    );
  }
}

/** Returns the full HTTP base URL for the gateway */
export function gatewayUrl(config: VaultConfig): string {
  return `http://${config.gatewayAddress}:${config.gatewayPort}`;
}

/** Returns the full HTTP base URL for a storage node */
export function nodeUrl(address: string, port: number): string {
  return `http://${address}:${port}`;
}
