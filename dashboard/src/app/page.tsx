'use client';

import React, { useEffect, useState } from 'react';

interface StorageNode {
  node_id: string;
  address: string;
  port: number;
  state: 'HEALTHY' | 'SUSPECTED' | 'FAILED' | 'RECOVERING' | 'DRAINING';
  last_heartbeat: string | null;
  storage_used: number;
  storage_total: number;
  registered_at: string;
}

interface VaultEvent {
  event_id: string;
  type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

interface ClusterStatus {
  nodes: StorageNode[];
  totalObjects: number;
  durableObjects: number;
  underReplicatedObjects: number;
  totalReplicas: number;
  healthyReplicas: number;
  corruptReplicas: number;
  pendingRepairJobs: number;
  recentEvents: VaultEvent[];
}

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8080';

export default function DashboardPage() {
  const [status, setStatus] = useState<ClusterStatus | null>(null);
  const [events, setEvents] = useState<VaultEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Poll or connect to SSE
  useEffect(() => {
    let sse: EventSource | null = null;

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${GATEWAY_URL}/cluster/status`);
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        setStatus(data);
        if (data.recentEvents) {
          setEvents(data.recentEvents);
        }
        setError(null);
      } catch (err: any) {
        setError(`Failed to connect to gateway at ${GATEWAY_URL}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);

    try {
      sse = new EventSource(`${GATEWAY_URL}/cluster/events/stream`);
      sse.onmessage = (e) => {
        try {
          const newEvents = JSON.parse(e.data);
          if (Array.isArray(newEvents)) {
            setEvents(newEvents);
          }
        } catch {}
      };
      sse.addEventListener('status', (e: any) => {
        try {
          const parsed = JSON.parse(e.data);
          setStatus(parsed);
        } catch {}
      });
      sse.onerror = () => {
        sse?.close();
      };
    } catch {}

    return () => {
      clearInterval(interval);
      if (sse) sse.close();
    };
  }, []);

  const triggerRepair = async () => {
    try {
      setActionMsg('Triggering repair scan...');
      const res = await fetch(`${GATEWAY_URL}/repairs/trigger`, { method: 'POST' });
      const data = await res.json();
      setActionMsg(`Repair scan triggered: ${data.message || 'Done'}`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (e: any) {
      setActionMsg(`Error triggering repair: ${e.message}`);
    }
  };

  const drainNode = async (nodeId: string) => {
    try {
      setActionMsg(`Requesting drain for node ${nodeId}...`);
      const res = await fetch(`${GATEWAY_URL}/nodes/${nodeId}/drain`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to drain');
      setActionMsg(`Drain initiated for ${nodeId}`);
      setTimeout(() => setActionMsg(null), 4000);
    } catch (e: any) {
      setActionMsg(`Error draining node: ${e.message}`);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'HEALTHY':
      case 'DURABLE':
      case 'DONE':
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'SUSPECTED':
      case 'UNDER_REPLICATED':
      case 'PENDING':
      case 'REPAIRING':
        return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
      case 'FAILED':
      case 'CORRUPT':
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
      case 'DRAINING':
        return 'text-sky-400 border-sky-500/30 bg-sky-500/10';
      default:
        return 'text-slate-400 border-slate-500/30 bg-slate-500/10';
    }
  };

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="text-purple-400">⚡</span> VAULT CLUSTER TELEMETRY
            </h1>
            <span className="px-2.5 py-0.5 text-xs rounded-full border border-purple-500/30 bg-purple-500/10 text-purple-300">
              R+W&gt;N Quorum
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Fault-Tolerant Distributed Object Storage System Monitor
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={triggerRepair}
            className="px-3 py-1.5 text-xs font-semibold rounded bg-purple-600 hover:bg-purple-500 text-white transition shadow-sm"
          >
            Trigger Replica Repair
          </button>
          <div className="text-xs px-3 py-1.5 rounded border border-slate-800 bg-slate-900/60 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${error ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'}`} />
            {error ? 'Gateway Offline' : 'Connected'}
          </div>
        </div>
      </header>

      {actionMsg && (
        <div className="px-4 py-2 text-xs rounded bg-purple-950/60 border border-purple-500/40 text-purple-200 animate-fade-in">
          {actionMsg}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm">
          {error}. Ensure the Vault Gateway is started on port 8080.
        </div>
      )}

      {/* Metric Cards */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Total Objects</span>
          <div className="text-2xl font-bold text-white mt-1">
            {status ? status.totalObjects : '—'}
          </div>
          <div className="text-xs text-emerald-400 mt-1">
            {status ? `${status.durableObjects} Durable` : ''}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Replication Health</span>
          <div className="text-2xl font-bold text-white mt-1">
            {status ? status.healthyReplicas : '—'}
            <span className="text-xs text-slate-500 font-normal"> / {status ? status.totalReplicas : '—'}</span>
          </div>
          <div className={`text-xs mt-1 ${status?.underReplicatedObjects ? 'text-amber-400' : 'text-slate-400'}`}>
            {status ? `${status.underReplicatedObjects} Under-replicated` : ''}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Storage Nodes</span>
          <div className="text-2xl font-bold text-white mt-1">
            {status ? status.nodes.filter(n => n.state === 'HEALTHY').length : '—'}
            <span className="text-xs text-slate-500 font-normal"> / {status ? status.nodes.length : '—'}</span>
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Healthy / Registered
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider">Active Repairs</span>
          <div className="text-2xl font-bold text-purple-300 mt-1">
            {status ? status.pendingRepairJobs : '—'}
          </div>
          <div className="text-xs text-rose-400 mt-1">
            {status ? `${status.corruptReplicas} Corrupt Replicas` : ''}
          </div>
        </div>
      </section>

      {/* Nodes Section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
          Cluster Storage Nodes
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {status?.nodes.map((node) => (
            <div
              key={node.node_id}
              className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-base">{node.node_id}</span>
                  <span className={`px-2 py-0.5 text-[10px] rounded-full border ${getStateColor(node.state)}`}>
                    {node.state}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1 font-mono">
                  {node.address}:{node.port}
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Storage Used</span>
                  <span>{(node.storage_used / 1024).toFixed(1)} KB</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-purple-500 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.max(5, (node.storage_used / (node.storage_total || 10485760)) * 100))}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>Last ping</span>
                  <span>
                    {node.last_heartbeat
                      ? `${Math.round((Date.now() - new Date(node.last_heartbeat).getTime()) / 1000)}s ago`
                      : 'Never'}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                <span className="text-[11px] text-slate-500">
                  Joined: {new Date(node.registered_at).toLocaleTimeString()}
                </span>
                {node.state !== 'DRAINING' && node.state !== 'FAILED' && (
                  <button
                    onClick={() => drainNode(node.node_id)}
                    className="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  >
                    Drain
                  </button>
                )}
              </div>
            </div>
          ))}

          {(!status || status.nodes.length === 0) && (
            <div className="col-span-3 p-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
              No nodes currently registered. Start storage nodes using <code>npm run start:node</code>.
            </div>
          )}
        </div>
      </section>

      {/* Live Event Log */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Cluster Event Audit Log
          </h2>
          <span className="text-xs text-slate-500">Real-time telemetry stream</span>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-slate-800 divide-y divide-slate-800/60 max-h-80 overflow-y-auto font-mono text-xs">
          {events.map((evt) => (
            <div key={evt.event_id} className="p-3 flex items-start justify-between gap-4 hover:bg-slate-800/30 transition">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-purple-300 text-[10px] font-bold">
                    {evt.type}
                  </span>
                  <span className="text-slate-300">{evt.message}</span>
                </div>
                {evt.payload && (
                  <pre className="text-[10px] text-slate-500 overflow-x-auto">
                    {JSON.stringify(evt.payload)}
                  </pre>
                )}
              </div>
              <span className="text-slate-500 text-[11px] whitespace-nowrap">
                {new Date(evt.created_at).toLocaleTimeString()}
              </span>
            </div>
          ))}

          {events.length === 0 && (
            <div className="p-6 text-center text-xs text-slate-500">
              No cluster events recorded yet.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
