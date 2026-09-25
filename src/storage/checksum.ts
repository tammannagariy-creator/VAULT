/**
 * storage/checksum.ts
 *
 * SHA-256 checksum utilities.
 *
 * A checksum is stored as "sha256:<hex>" so the algorithm is always explicit.
 * This makes it safe to change the algorithm later without silent migration issues.
 *
 * Key principle (System Invariant SI-02):
 *   A successful disk read does NOT mean the data is correct.
 *   Every read path MUST call verifyChecksum() before returning data to a client.
 */

import { createHash } from 'crypto';

const PREFIX = 'sha256:';

/**
 * Compute the SHA-256 checksum of a Buffer.
 * Returns the string in the format "sha256:<64-char hex>"
 */
export function computeChecksum(data: Buffer): string {
  const hash = createHash('sha256').update(data).digest('hex');
  return `${PREFIX}${hash}`;
}

/**
 * Verify that the data matches the expected checksum.
 * Returns true if the data is intact, false if it has been corrupted.
 */
export function verifyChecksum(data: Buffer, expected: string): boolean {
  if (!expected.startsWith(PREFIX)) {
    // Unknown algorithm — cannot verify. Treat as failure.
    return false;
  }
  const actual = computeChecksum(data);
  return actual === expected;
}

/**
 * Extract just the hex part from a "sha256:<hex>" string.
 * Useful for display purposes only.
 */
export function extractHex(checksum: string): string {
  return checksum.startsWith(PREFIX) ? checksum.slice(PREFIX.length) : checksum;
}
