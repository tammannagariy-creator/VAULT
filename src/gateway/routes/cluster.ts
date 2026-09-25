/**
 * gateway/routes/cluster.ts
 *
 * Cluster-level monitoring APIs:
 *   GET /cluster/status    — full cluster health snapshot
 *   GET /cluster/events    — recent event log
 *   GET /health            — gateway health check
 *   GET /cluster/events/stream — SSE stream for live dashboard
 */

import { Router, Request, Response } from 'express';
import type { MetadataService } from '../../metadata/service.js';

export function clusterRouter(metadata: MetadataService): Router {
  const router = Router();

  // ─── GET /health and / ────────────────────────────────────────────────────

  const healthHandler = (_req: Request, res: Response) => {
    res.json({
      status: 'UP',
      service: 'vault-gateway',
      uptime: Math.round(process.uptime()),
      timestamp: new Date().toISOString(),
    });
  };

  router.get('/health', healthHandler);
  router.get('/', healthHandler);

  // ─── GET /cluster/status ──────────────────────────────────────────────────

  router.get('/status', (_req: Request, res: Response) => {
    const status = metadata.getClusterStatus();
    res.json(status);
  });

  // ─── GET /cluster/config ──────────────────────────────────────────────────

  router.get('/config', (_req: Request, res: Response) => {
    res.json({
      replicationFactor: (global as any).__vaultConfig?.replicationFactor ?? 3,
      writeQuorum: (global as any).__vaultConfig?.writeQuorum ?? 2,
      readQuorum: (global as any).__vaultConfig?.readQuorum ?? 2,
      heartbeatInterval: (global as any).__vaultConfig?.heartbeatInterval ?? 5000,
      heartbeatTimeout: (global as any).__vaultConfig?.heartbeatTimeout ?? 15000,
      repairInterval: (global as any).__vaultConfig?.repairInterval ?? 10000,
      scanInterval: (global as any).__vaultConfig?.scanInterval ?? 60000,
      checksumAlgorithm: (global as any).__vaultConfig?.checksumAlgorithm ?? 'sha256',
      metadataDatabase: (global as any).__vaultConfig?.metadataDatabase ?? './vault.db',
    });
  });

  // ─── GET /cluster/events ──────────────────────────────────────────────────

  router.get('/events', (req: Request, res: Response) => {
    const limit = Math.min(parseInt(String(req.query.limit ?? '50'), 10), 200);
    const events = metadata.getRecentEvents(limit);
    res.json({ events, count: events.length });
  });

  // ─── GET /cluster/events/stream — Server-Sent Events (SSE) ───────────────
  //
  // The dashboard subscribes to this endpoint for live event updates.
  // Every 2 seconds we push the latest 10 events.
  // This is simpler than WebSockets and works natively in browsers.

  router.get('/events/stream', (req: Request, res: Response) => {
    res.set({
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    res.flushHeaders();

    let lastEventId: string | null = null;

    const intervalId = setInterval(() => {
      try {
        const events = metadata.getRecentEvents(10);
        if (events.length > 0 && events[0].event_id !== lastEventId) {
          lastEventId = events[0].event_id;
          const data = JSON.stringify(events);
          res.write(`data: ${data}\n\n`);
        }

        // Also push cluster status every 5 seconds
        const status = metadata.getClusterStatus();
        res.write(`event: status\ndata: ${JSON.stringify(status)}\n\n`);
      } catch {
        // Client disconnected
        clearInterval(intervalId);
      }
    }, 2000);

    req.on('close', () => {
      clearInterval(intervalId);
    });
  });

  return router;
}
