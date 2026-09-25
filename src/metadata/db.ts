/**
 * metadata/db.ts
 *
 * SQLite database setup using Node.js built-in `node:sqlite` module.
 * Available in Node.js 22.5+ (stable in Node 24).
 *
 * Why Node.js built-in SQLite?
 *   - Zero dependencies (no native compilation, no Windows build tools needed)
 *   - Synchronous API (same pattern as better-sqlite3)
 *   - ACID transactions
 *   - WAL mode for concurrent reads
 *   - Runs everywhere Node 22+ is installed
 *
 * We wrap the built-in in a thin compatibility shim so the MetadataService
 * code is clean and doesn't depend on the raw sqlite API.
 */

import { DatabaseSync } from 'node:sqlite';
import path from 'path';
import fs from 'fs';

// ─── Database Wrapper ─────────────────────────────────────────────────────────
// Provides a familiar interface matching the better-sqlite3 API shape
// so the MetadataService can call .prepare().get() / .run() / .all()

export interface PreparedStatement {
  get: (...args: unknown[]) => Record<string, unknown> | undefined;
  all: (...args: unknown[]) => Record<string, unknown>[];
  run: (...args: unknown[]) => { changes: number; lastInsertRowid: number | bigint };
}

export class VaultDatabase {
  private db: DatabaseSync;

  constructor(dbPath: string) {
    const dir = path.dirname(dbPath);
    if (dir !== '.' && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // node:sqlite DatabaseSync opens/creates the file
    this.db = new DatabaseSync(dbPath);

    // Enable WAL mode and foreign keys
    this.db.exec('PRAGMA journal_mode = WAL');
    this.db.exec('PRAGMA foreign_keys = ON');
    this.db.exec('PRAGMA synchronous = NORMAL');
  }

  /** Execute raw SQL (for DDL migrations) */
  exec(sql: string): void {
    this.db.exec(sql);
  }

  /** Prepare a statement for repeated use */
  prepare(sql: string): PreparedStatement {
    const stmt = this.db.prepare(sql);
    return {
      get: (...args: unknown[]) => stmt.get(...(args as Parameters<typeof stmt.get>)) as Record<string, unknown> | undefined,
      all: (...args: unknown[]) => stmt.all(...(args as Parameters<typeof stmt.all>)) as Record<string, unknown>[],
      run: (...args: unknown[]) => stmt.run(...(args as Parameters<typeof stmt.run>)) as { changes: number; lastInsertRowid: number | bigint },
    };
  }

  /** Close the database */
  close(): void {
    this.db.close();
  }
}

// ─── Schema Migrations ────────────────────────────────────────────────────────

export function createDatabase(dbPath: string): VaultDatabase {
  const db = new VaultDatabase(dbPath);
  runMigrations(db);
  return db;
}

function runMigrations(db: VaultDatabase): void {
  db.exec(`
    -- ─────────────────────────────────────────────────────────────────────────
    -- NODES
    -- ─────────────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS nodes (
      node_id        TEXT PRIMARY KEY,
      address        TEXT NOT NULL,
      port           INTEGER NOT NULL,
      state          TEXT NOT NULL DEFAULT 'HEALTHY',
      last_heartbeat TEXT,
      storage_used   INTEGER NOT NULL DEFAULT 0,
      storage_total  INTEGER NOT NULL DEFAULT 0,
      registered_at  TEXT NOT NULL
    );

    -- ─────────────────────────────────────────────────────────────────────────
    -- OBJECTS
    -- ─────────────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS objects (
      object_id          TEXT PRIMARY KEY,
      logical_key        TEXT UNIQUE NOT NULL,
      version            INTEGER NOT NULL DEFAULT 1,
      size               INTEGER NOT NULL,
      checksum           TEXT NOT NULL,
      replication_factor INTEGER NOT NULL DEFAULT 3,
      placement_epoch    INTEGER NOT NULL DEFAULT 1,
      state              TEXT NOT NULL DEFAULT 'PENDING',
      created_at         TEXT NOT NULL,
      updated_at         TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_objects_key   ON objects(logical_key);
    CREATE INDEX IF NOT EXISTS idx_objects_state ON objects(state);

    -- ─────────────────────────────────────────────────────────────────────────
    -- REPLICAS
    -- ─────────────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS replicas (
      replica_id       TEXT PRIMARY KEY,
      object_id        TEXT NOT NULL,
      node_id          TEXT NOT NULL,
      version          INTEGER NOT NULL,
      checksum         TEXT NOT NULL,
      size             INTEGER NOT NULL,
      state            TEXT NOT NULL DEFAULT 'HEALTHY',
      last_verified_at TEXT,
      created_at       TEXT NOT NULL,
      UNIQUE(object_id, node_id)
    );

    CREATE INDEX IF NOT EXISTS idx_replicas_object  ON replicas(object_id);
    CREATE INDEX IF NOT EXISTS idx_replicas_node    ON replicas(node_id);
    CREATE INDEX IF NOT EXISTS idx_replicas_state   ON replicas(state);

    -- ─────────────────────────────────────────────────────────────────────────
    -- REPAIR_JOBS
    -- ─────────────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS repair_jobs (
      job_id         TEXT PRIMARY KEY,
      object_id      TEXT NOT NULL,
      replica_id     TEXT,
      target_node_id TEXT NOT NULL,
      source_node_id TEXT NOT NULL,
      state          TEXT NOT NULL DEFAULT 'PENDING',
      reason         TEXT NOT NULL,
      created_at     TEXT NOT NULL,
      updated_at     TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_repair_state  ON repair_jobs(state);
    CREATE INDEX IF NOT EXISTS idx_repair_object ON repair_jobs(object_id);

    -- ─────────────────────────────────────────────────────────────────────────
    -- EVENTS
    -- ─────────────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS events (
      event_id   TEXT PRIMARY KEY,
      type       TEXT NOT NULL,
      message    TEXT NOT NULL,
      payload    TEXT,
      created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
    CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at);
  `);
}
