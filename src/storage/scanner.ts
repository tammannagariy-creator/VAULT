/**
 * storage/scanner.ts
 *
 * IntegrityScanner — periodically reads all stored objects and verifies
 * their checksums against the expected values stored in their sidecar files.
 *
 * Problem this solves:
 *   Silent data corruption ("bit rot") — the disk returns data without error,
 *   but the data has changed due to hardware faults or cosmic rays.
 *   A successful read does NOT mean the data is correct.
 *
 * Implementation:
 *   - Each stored object has a companion .meta file containing its expected checksum.
 *   - The scanner reads each .dat file, computes its checksum, and compares.
 *   - If mismatch → marks the replica CORRUPT on the gateway metadata.
 *   - The repair worker then picks it up and creates a replacement.
 *
 * The scanner runs as a background interval inside the storage node process.
 * Results are reported to the gateway via HTTP.
 */

import { ObjectStore } from './store.js';
import { computeChecksum } from './checksum.js';
import axios from 'axios';
import fs from 'fs';
import path from 'path';

interface ScannerConfig {
  nodeId: string;
  storageBasePath: string;
  gatewayAddress: string;
  gatewayPort: number;
  scanInterval: number; // milliseconds
}

interface ObjectSidecar {
  checksum: string;
  object_id: string;
  version: number;
}

export class IntegrityScanner {
  private config: ScannerConfig;
  private store: ObjectStore;
  private timer: ReturnType<typeof setInterval> | null = null;
  private isRunning = false;

  constructor(config: ScannerConfig, store: ObjectStore) {
    this.config = config;
    this.store = store;
  }

  start(): void {
    console.log(`[Scanner] Starting integrity scanner (interval: ${this.config.scanInterval}ms)`);
    this.timer = setInterval(() => this.scan(), this.config.scanInterval);
    // Run an initial scan after 30 seconds to allow the cluster to stabilize
    setTimeout(() => this.scan(), 30_000);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  async scan(): Promise<void> {
    if (this.isRunning) return; // Don't overlap scans
    this.isRunning = true;

    const objectIds = this.store.listObjectIds();
    console.log(`[Scanner] Starting scan of ${objectIds.length} objects`);

    let corrupt = 0;
    let ok = 0;

    for (const objectId of objectIds) {
      try {
        const sidecar = this.readSidecar(objectId);
        if (!sidecar) continue; // No sidecar = no expected checksum; skip

        const data = this.store.read(objectId);
        if (!data) continue; // File disappeared; skip

        const actual = computeChecksum(data);

        if (actual !== sidecar.checksum) {
          console.warn(`[Scanner] CORRUPT: object ${objectId} — expected ${sidecar.checksum}, got ${actual}`);
          await this.reportCorruption(objectId, sidecar.checksum, actual);
          corrupt++;
        } else {
          ok++;
        }
      } catch (err) {
        console.error(`[Scanner] Error scanning object ${objectId}:`, err);
      }
    }

    console.log(`[Scanner] Scan complete: ${ok} OK, ${corrupt} CORRUPT`);
    this.isRunning = false;
  }

  /**
   * Write a sidecar file for a newly stored object.
   * Called by the storage node after a successful write.
   */
  static writeSidecar(basePath: string, objectId: string, sidecar: ObjectSidecar): void {
    const sidecarPath = path.join(basePath, `${objectId}.meta`);
    fs.writeFileSync(sidecarPath, JSON.stringify(sidecar), 'utf-8');
  }

  private readSidecar(objectId: string): ObjectSidecar | null {
    const sidecarPath = path.join(this.config.storageBasePath, `${objectId}.meta`);
    if (!fs.existsSync(sidecarPath)) return null;
    try {
      return JSON.parse(fs.readFileSync(sidecarPath, 'utf-8')) as ObjectSidecar;
    } catch {
      return null;
    }
  }

  private async reportCorruption(objectId: string, expected: string, actual: string): Promise<void> {
    try {
      await axios.post(
        `http://${this.config.gatewayAddress}:${this.config.gatewayPort}/internal/corruption`,
        {
          node_id: this.config.nodeId,
          object_id: objectId,
          expected_checksum: expected,
          actual_checksum: actual,
        },
        { timeout: 5000 }
      );
    } catch (err) {
      console.error(`[Scanner] Failed to report corruption to gateway:`, err);
    }
  }
}
