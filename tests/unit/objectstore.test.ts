/**
 * tests/unit/objectstore.test.ts
 *
 * Unit tests for the ObjectStore (physical file storage).
 * Uses a temporary directory that is cleaned up after each test.
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { ObjectStore } from '../../src/storage/store';

describe('ObjectStore', () => {
  let tmpDir: string;
  let store: ObjectStore;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'vault-test-'));
    store = new ObjectStore(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  test('writes and reads back identical data', () => {
    const data = Buffer.from('hello vault');
    store.write('obj-1', data);
    const retrieved = store.read('obj-1');
    expect(retrieved).toEqual(data);
  });

  test('returns null for non-existent object', () => {
    expect(store.read('does-not-exist')).toBeNull();
  });

  test('exists returns true after write', () => {
    store.write('obj-2', Buffer.from('data'));
    expect(store.exists('obj-2')).toBe(true);
  });

  test('exists returns false before write', () => {
    expect(store.exists('not-written')).toBe(false);
  });

  test('delete removes the file', () => {
    store.write('obj-3', Buffer.from('deleteme'));
    expect(store.exists('obj-3')).toBe(true);
    store.delete('obj-3');
    expect(store.exists('obj-3')).toBe(false);
    expect(store.read('obj-3')).toBeNull();
  });

  test('delete returns false for non-existent file', () => {
    expect(store.delete('ghost')).toBe(false);
  });

  test('listObjectIds returns all stored objects', () => {
    store.write('a', Buffer.from('1'));
    store.write('b', Buffer.from('2'));
    store.write('c', Buffer.from('3'));
    const ids = store.listObjectIds();
    expect(ids.sort()).toEqual(['a', 'b', 'c']);
  });

  test('overwrite replaces previous data', () => {
    store.write('obj-4', Buffer.from('version 1'));
    store.write('obj-4', Buffer.from('version 2'));
    const data = store.read('obj-4');
    expect(data?.toString()).toBe('version 2');
  });

  test('temp files from previous crashes are cleaned on init', () => {
    // Create a leftover .tmp file
    fs.writeFileSync(path.join(tmpDir, 'leaked.tmp'), 'garbage');
    // Re-create the store (triggers cleanup)
    const store2 = new ObjectStore(tmpDir);
    expect(fs.existsSync(path.join(tmpDir, 'leaked.tmp'))).toBe(false);
  });

  test('getSize returns correct byte count', () => {
    const data = Buffer.from('size test data');
    store.write('obj-5', data);
    expect(store.getSize('obj-5')).toBe(data.length);
  });

  test('getSize returns -1 for non-existent', () => {
    expect(store.getSize('missing')).toBe(-1);
  });
});
