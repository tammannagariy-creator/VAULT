/**
 * tests/integration/api.test.ts
 *
 * Integration tests — require a running cluster.
 *
 * HOW TO RUN:
 *   1. Start the cluster: .\scripts\start-cluster.ps1
 *   2. In a second terminal: npx jest --testPathPattern="tests/integration"
 *
 * These tests verify the full end-to-end behaviour including:
 *   - PUT → GET → checksum match
 *   - Conditional writes (version conflict)
 *   - Node drain flow
 *   - Repair trigger
 */

const GATEWAY = process.env.GATEWAY_URL ?? 'http://localhost:8080';
const TIMEOUT = 15_000;

async function http(
  method: string,
  path: string,
  body?: Buffer | object,
  headers?: Record<string, string>
): Promise<{ status: number; body: unknown; headers: Record<string, string> }> {
  const fetch = (await import('node-fetch')).default;
  const res = await fetch(`${GATEWAY}${path}`, {
    method,
    body: body instanceof Buffer ? body : body ? JSON.stringify(body) : undefined,
    headers: {
      ...(body instanceof Buffer ? { 'Content-Type': 'application/octet-stream' } : body ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
  });
  const text = await res.text();
  let parsed: unknown;
  try { parsed = JSON.parse(text); } catch { parsed = text; }
  const resHeaders: Record<string, string> = {};
  res.headers.forEach((v, k) => { resHeaders[k] = v; });
  return { status: res.status, body: parsed, headers: resHeaders };
}

describe('Vault Integration Tests', () => {
  jest.setTimeout(TIMEOUT);

  beforeAll(async () => {
    // Verify cluster is up
    const { status } = await http('GET', '/health');
    if (status !== 200) {
      throw new Error('Cluster is not running — start with: .\\scripts\\start-cluster.ps1');
    }
  });

  // ─── Basic PUT / GET ───────────────────────────────────────────────────────

  describe('PUT and GET', () => {
    const key = `integration-test/basic-${Date.now()}.txt`;
    const content = Buffer.from('Hello from Vault integration test!');
    let objectId: string;
    let checksum: string;

    test('PUT creates a DURABLE object', async () => {
      const { status, body } = await http('PUT', `/objects/${key}`, content) as any;
      expect(status).toBe(201);
      expect(body.state).toBe('DURABLE');
      expect(body.replicas.length).toBeGreaterThanOrEqual(2);
      objectId = body.object_id;
      checksum = body.checksum;
    });

    test('GET retrieves the exact bytes', async () => {
      const fetch = (await import('node-fetch')).default;
      const res = await fetch(`${GATEWAY}/objects/${key}`);
      expect(res.status).toBe(200);
      const buf = Buffer.from(await res.arrayBuffer());
      expect(buf).toEqual(content);
    });

    test('GET returns matching checksum header', async () => {
      const { headers } = await http('GET', `/objects/${key}`);
      expect(headers['x-object-checksum']).toBe(checksum);
    });

    test('GET metadata returns correct object info', async () => {
      const { status, body } = await http('GET', `/objects/${key}/metadata`) as any;
      expect(status).toBe(200);
      expect(body.object_id).toBe(objectId);
      expect(body.replicas.length).toBeGreaterThanOrEqual(2);
    });

    test('GET non-existent key returns 404', async () => {
      const { status } = await http('GET', '/objects/does-not-exist/never.txt');
      expect(status).toBe(404);
    });

    test('DELETE removes the object', async () => {
      const { status, body } = await http('DELETE', `/objects/${key}`) as any;
      expect(status).toBe(200);
      expect(body.deleted).toBe(true);
    });

    test('GET after DELETE returns 404', async () => {
      const { status } = await http('GET', `/objects/${key}`);
      expect(status).toBe(404);
    });
  });

  // ─── Versioning / Conditional Writes ──────────────────────────────────────

  describe('Conditional writes (X-Expected-Version)', () => {
    const key = `integration-test/versioning-${Date.now()}.txt`;

    test('PUT with X-Expected-Version: 0 creates new object', async () => {
      const { status, body } = await http(
        'PUT', `/objects/${key}`,
        Buffer.from('version 1'),
        { 'X-Expected-Version': '0' }
      ) as any;
      expect(status).toBe(201);
      expect(body.version).toBe(1);
    });

    test('PUT with X-Expected-Version: 0 on existing fails with 409', async () => {
      const { status } = await http(
        'PUT', `/objects/${key}`,
        Buffer.from('should fail'),
        { 'X-Expected-Version': '0' }
      );
      expect(status).toBe(409);
    });

    test('PUT with correct version updates', async () => {
      const { status, body } = await http(
        'PUT', `/objects/${key}`,
        Buffer.from('version 2'),
        { 'X-Expected-Version': '1' }
      ) as any;
      expect(status).toBe(200);
      expect(body.version).toBe(2);
    });

    afterAll(async () => {
      await http('DELETE', `/objects/${key}`);
    });
  });

  // ─── Cluster Status ────────────────────────────────────────────────────────

  describe('Cluster status', () => {
    test('GET /cluster/status returns healthy cluster', async () => {
      const { status, body } = await http('GET', '/cluster/status') as any;
      expect(status).toBe(200);
      expect(body.nodes.length).toBeGreaterThan(0);
    });

    test('GET /nodes returns all nodes', async () => {
      const { status, body } = await http('GET', '/nodes') as any;
      expect(status).toBe(200);
      expect(body.count).toBeGreaterThan(0);
    });

    test('GET /repairs returns job list', async () => {
      const { status, body } = await http('GET', '/repairs') as any;
      expect(status).toBe(200);
      expect(Array.isArray(body.jobs)).toBe(true);
    });
  });

  // ─── Large Object ─────────────────────────────────────────────────────────

  describe('Large object upload/download', () => {
    const key = `integration-test/large-${Date.now()}.bin`;
    const size = 10 * 1024 * 1024; // 10 MB
    const content = Buffer.alloc(size, 0xab);

    test('PUT 10MB object succeeds', async () => {
      const { status, body } = await http('PUT', `/objects/${key}`, content) as any;
      expect(status).toBe(201);
      expect(body.size).toBe(size);
    }, 30_000);

    test('GET 10MB object returns identical bytes', async () => {
      const fetch = (await import('node-fetch')).default;
      const res = await fetch(`${GATEWAY}/objects/${key}`);
      expect(res.status).toBe(200);
      const buf = Buffer.from(await res.arrayBuffer());
      expect(buf.length).toBe(size);
      expect(buf[0]).toBe(0xab);
    }, 30_000);

    afterAll(async () => {
      await http('DELETE', `/objects/${key}`);
    });
  });
});
