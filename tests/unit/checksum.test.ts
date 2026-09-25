/**
 * tests/unit/checksum.test.ts
 *
 * Unit tests for the checksum module.
 * These tests verify correctness of our primary data integrity mechanism.
 */

import { computeChecksum, verifyChecksum, extractHex } from '../../src/storage/checksum';

describe('Checksum', () => {
  const testData = Buffer.from('Hello, Vault!');

  test('computeChecksum returns sha256: prefix', () => {
    const checksum = computeChecksum(testData);
    expect(checksum).toMatch(/^sha256:[a-f0-9]{64}$/);
  });

  test('computeChecksum is deterministic', () => {
    expect(computeChecksum(testData)).toBe(computeChecksum(testData));
  });

  test('computeChecksum differs for different data', () => {
    const other = Buffer.from('Corrupt data!');
    expect(computeChecksum(testData)).not.toBe(computeChecksum(other));
  });

  test('verifyChecksum returns true for correct data', () => {
    const checksum = computeChecksum(testData);
    expect(verifyChecksum(testData, checksum)).toBe(true);
  });

  test('verifyChecksum returns false for corrupted data', () => {
    const checksum = computeChecksum(testData);
    const corrupt = Buffer.from('Corrupted!');
    expect(verifyChecksum(corrupt, checksum)).toBe(false);
  });

  test('verifyChecksum returns false for unknown algorithm', () => {
    expect(verifyChecksum(testData, 'md5:abc123')).toBe(false);
  });

  test('verifyChecksum returns false for empty expected', () => {
    expect(verifyChecksum(testData, '')).toBe(false);
  });

  test('extractHex strips the prefix', () => {
    const checksum = computeChecksum(testData);
    const hex = extractHex(checksum);
    expect(hex).toHaveLength(64);
    expect(hex).not.toContain('sha256:');
  });

  test('empty buffer has a stable checksum', () => {
    const empty = Buffer.alloc(0);
    const checksum = computeChecksum(empty);
    expect(checksum).toBe(
      'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    );
  });
});
