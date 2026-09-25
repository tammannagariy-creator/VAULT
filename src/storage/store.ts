/**
 * storage/store.ts
 *
 * Physical file storage for a single storage node.
 *
 * Each object is stored as a file at:
 *   <storageBasePath>/<object_id>.dat
 *
 * Atomic write pattern (System Invariant SI-05):
 *   1. Write data to a temp file: <object_id>.tmp
 *   2. fsync the temp file (ensures data is on disk, not just in OS buffer)
 *   3. Rename temp → final (atomic on both Linux and Windows with NTFS)
 *
 * This prevents partial writes from being visible as complete objects.
 * A crash after step 2 but before step 3 leaves a .tmp file that is safe to ignore.
 *
 * Reads are straightforward — read the file and return raw bytes.
 * The caller (Coordinator) is responsible for checksum verification.
 */

import fs from 'fs';
import path from 'path';

export class ObjectStore {
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
    if (!fs.existsSync(basePath)) {
      fs.mkdirSync(basePath, { recursive: true });
    }
    this.cleanupTempFiles();
  }

  /**
   * Write an object to disk atomically.
   * Returns the actual number of bytes written.
   */
  write(objectId: string, data: Buffer): void {
    const finalPath = this.objectPath(objectId);
    const tmpPath = this.tmpPath(objectId);

    // Step 1: write to temp file
    const fd = fs.openSync(tmpPath, 'w');
    try {
      fs.writeSync(fd, data);
      // Step 2: fsync — wait until the OS flushes to disk
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }

    // Step 3: atomic rename (POSIX rename is atomic; Windows uses MoveFileEx)
    fs.renameSync(tmpPath, finalPath);
  }

  /**
   * Read an object from disk.
   * Returns null if the file does not exist.
   * Does NOT verify the checksum — that is the Coordinator's responsibility.
   */
  read(objectId: string): Buffer | null {
    const filePath = this.objectPath(objectId);
    if (!fs.existsSync(filePath)) {
      return null;
    }
    return fs.readFileSync(filePath);
  }

  /**
   * Delete an object from disk.
   * Returns true if the file existed and was deleted, false otherwise.
   */
  delete(objectId: string): boolean {
    const filePath = this.objectPath(objectId);
    if (!fs.existsSync(filePath)) {
      return false;
    }
    fs.unlinkSync(filePath);
    return true;
  }

  /**
   * Check if an object exists on this node.
   */
  exists(objectId: string): boolean {
    return fs.existsSync(this.objectPath(objectId));
  }

  /**
   * List all object IDs stored on this node.
   * Used by the integrity scanner.
   */
  listObjectIds(): string[] {
    const files = fs.readdirSync(this.basePath);
    return files
      .filter(f => f.endsWith('.dat'))
      .map(f => f.slice(0, -4)); // strip .dat
  }

  /**
   * Get the size of a stored object in bytes.
   * Returns -1 if the file doesn't exist.
   */
  getSize(objectId: string): number {
    const filePath = this.objectPath(objectId);
    try {
      const stat = fs.statSync(filePath);
      return stat.size;
    } catch {
      return -1;
    }
  }

  /**
   * Get approximate storage usage of this node's data directory.
   */
  getStorageUsed(): number {
    try {
      const files = fs.readdirSync(this.basePath);
      return files.reduce((total, file) => {
        try {
          const stat = fs.statSync(path.join(this.basePath, file));
          return total + stat.size;
        } catch {
          return total;
        }
      }, 0);
    } catch {
      return 0;
    }
  }

  private objectPath(objectId: string): string {
    return path.join(this.basePath, `${objectId}.dat`);
  }

  private tmpPath(objectId: string): string {
    return path.join(this.basePath, `${objectId}.tmp`);
  }

  /**
   * Clean up any leftover .tmp files from crashed writes.
   * Called once at startup — these are safe to delete.
   */
  private cleanupTempFiles(): void {
    try {
      const files = fs.readdirSync(this.basePath);
      for (const file of files) {
        if (file.endsWith('.tmp')) {
          fs.unlinkSync(path.join(this.basePath, file));
        }
      }
    } catch {
      // Ignore errors during cleanup
    }
  }
}
