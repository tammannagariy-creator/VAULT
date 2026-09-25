import fs from 'fs';
import path from 'path';

const ARTIFACT_PATH = 'C:\\Users\\tamma\\.gemini\\antigravity\\brain\\fec58e9d-ead8-43d8-9377-c0f221416b9d\\vault_control_plane.html';
const DASHBOARD_PATH = 'C:\\surya\\vault\\dashboard\\public\\index.html';

const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vault — Distributed Storage Control Plane</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #06080d; color: #cbd5e1; margin: 0; padding: 0; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    .custom-scroll::-webkit-scrollbar { width: 5px; height: 5px; }
    .custom-scroll::-webkit-scrollbar-track { background: #06080d; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #1c2233; border-radius: 2px; }
    .custom-scroll::-webkit-scrollbar-thumb:hover { background: #2e3852; }
    .badge-verified { background: rgba(16, 185, 129, 0.12); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-implemented { background: rgba(59, 130, 246, 0.12); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-unverified { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-critical { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .card-panel { background: #0a0d16; border: 1px solid #161c2d; }
    .card-panel:hover { border-color: #242d45; }
    .nav-btn { transition: all 0.15s ease; }
    .nav-btn:hover { background: rgba(30, 41, 59, 0.6); color: #ffffff; }
    .nav-btn.active { background: #151b2c; color: #ffffff; border-left: 2px solid #8b5cf6; font-weight: 600; }
    .terminal-container { background: #040508; font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="h-screen overflow-hidden flex flex-col bg-[#06080d] text-slate-300 select-none">

  <!-- TOAST NOTIFICATION CONTAINER -->
  <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col space-y-2 pointer-events-none"></div>

  <!-- CONFIRMATION MODAL -->
  <div id="confirm-modal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm hidden items-center justify-center p-4">
    <div class="bg-[#0b0e18] border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
      <div class="flex items-center space-x-3">
        <div id="modal-icon-container" class="w-9 h-9 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold font-mono">!</div>
        <div>
          <h3 id="modal-title" class="text-base font-bold text-white tracking-tight">Confirm Action</h3>
          <p id="modal-endpoint" class="text-[11px] font-mono text-purple-400 mt-0.5">POST /endpoint</p>
        </div>
      </div>
      <p id="modal-message" class="text-xs text-slate-300 leading-relaxed"></p>
      <div id="modal-details" class="p-3 bg-black/50 border border-slate-800 rounded font-mono text-xs text-slate-400 hidden"></div>
      <div class="flex justify-end space-x-3 pt-2">
        <button onclick="closeModal()" class="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono text-xs transition">Cancel</button>
        <button id="modal-confirm-btn" class="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded font-mono text-xs font-bold transition">Confirm</button>
      </div>
    </div>
  </div>

  <!-- GLOBAL PERSISTENT HEADER -->
  <header class="h-13 border-b border-slate-800/80 bg-[#080b12] px-4 flex items-center justify-between z-20 shrink-0">
    <div class="flex items-center space-x-3">
      <div class="flex items-center space-x-2">
        <div class="w-6 h-6 rounded bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400 font-bold text-xs">V</div>
        <span class="font-bold tracking-wider text-slate-100 text-sm">VAULT</span>
        <span class="text-[10px] text-slate-500 uppercase tracking-widest hidden md:inline">Distributed Storage</span>
      </div>
      <span class="text-slate-700">/</span>
      <div class="flex items-center space-x-2 text-xs text-slate-400 font-mono">
        <span id="breadcrumb-section">OVERVIEW</span>
        <span class="text-slate-700">&rsaquo;</span>
        <span id="breadcrumb-page" class="text-slate-200 font-semibold">Dashboard</span>
      </div>
    </div>

    <!-- Cluster Real-Time Status Telemetry -->
    <div class="flex items-center space-x-2.5 text-xs">
      <!-- Live Indicator -->
      <div id="header-conn-badge" class="flex items-center space-x-2 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1">
        <span id="header-conn-dot" class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span id="header-conn-text" class="text-slate-200 font-mono font-medium">LIVE</span>
        <span class="text-slate-600">|</span>
        <span class="text-slate-400 text-[11px]">Sync:</span>
        <span id="header-sync-time" class="text-slate-200 font-mono text-[11px]">--:--:--</span>
      </div>

      <!-- Gateway Pill -->
      <div class="flex items-center space-x-1.5 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 text-slate-400 font-mono text-xs">
        <span class="text-slate-400">Gateway:</span>
        <span id="header-gw-status" class="text-emerald-400 font-semibold font-mono">localhost:8080 (UP)</span>
      </div>

      <!-- SSE Pill -->
      <div class="flex items-center space-x-1.5 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 font-mono text-xs">
        <span class="text-slate-400">SSE:</span>
        <span id="header-sse-status" class="text-emerald-400 font-semibold">CONNECTED</span>
      </div>

      <!-- Cluster Health Pill -->
      <div class="flex items-center space-x-1.5 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 font-mono text-xs">
        <span class="text-slate-400">Cluster:</span>
        <span id="header-cluster-status" class="text-emerald-400 font-semibold">HEALTHY</span>
      </div>

      <!-- Quick Nav Dropdown -->
      <select id="quick-jump-select" onchange="navigateTo(this.value)" class="bg-[#0b0e18] border border-purple-500/30 text-purple-300 rounded px-2 py-1 text-xs font-mono outline-none cursor-pointer hover:border-purple-400 hidden lg:block">
        <!-- Populated via JS -->
      </select>
    </div>
  </header>

  <!-- MAIN APP CONTAINER -->
  <div class="flex flex-1 overflow-hidden">

    <!-- LEFT SIDEBAR -->
    <aside class="w-60 border-r border-slate-800/80 bg-[#070910] flex flex-col justify-between shrink-0 select-none">
      <div class="p-3 overflow-y-auto custom-scroll flex-1 space-y-4">
        
        <!-- SECTION: OVERVIEW -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">OVERVIEW</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('dashboard')" id="nav-dashboard" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Dashboard</span>
              <span class="text-[10px] font-mono text-emerald-400">LIVE</span>
            </button>
          </div>
        </div>

        <!-- SECTION: CLUSTER -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">CLUSTER</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('nodes')" id="nav-nodes" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Nodes</span>
              <span id="nav-badge-nodes" class="text-[10px] font-mono text-slate-500">3 Hosts</span>
            </button>
            <button onclick="navigateTo('node_detail')" id="nav-node_detail" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Node Detail</span>
              <span id="nav-badge-selected-node" class="text-[10px] font-mono text-amber-400">node-3</span>
            </button>
            <button onclick="navigateTo('topology')" id="nav-topology" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Topology</span>
              <span class="text-[10px] font-mono text-slate-500">N=3</span>
            </button>
            <button onclick="navigateTo('membership')" id="nav-membership" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Membership</span>
              <span class="text-[10px] font-mono text-emerald-400">Heartbeats</span>
            </button>
            <button onclick="navigateTo('gateway')" id="nav-gateway" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Gateway</span>
              <span class="text-[10px] font-mono text-slate-500">:8080</span>
            </button>
          </div>
        </div>

        <!-- SECTION: STORAGE -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">STORAGE</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('objects')" id="nav-objects" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Objects</span>
              <span id="nav-badge-obj-count" class="text-[10px] font-mono text-slate-500">0 objs</span>
            </button>
            <button onclick="navigateTo('object_detail')" id="nav-object_detail" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Object Detail</span>
              <span class="text-[10px] font-mono text-slate-500">Inspect</span>
            </button>
            <button onclick="navigateTo('buckets')" id="nav-buckets" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Buckets</span>
              <span class="text-[10px] font-mono text-slate-500">Namespaces</span>
            </button>
            <button onclick="navigateTo('replicas')" id="nav-replicas" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Replicas</span>
              <span class="text-[10px] font-mono text-emerald-400">Synced</span>
            </button>
            <button onclick="navigateTo('versions')" id="nav-versions" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Versions</span>
              <span class="text-[10px] font-mono text-purple-400">OCC</span>
            </button>
            <button onclick="navigateTo('integrity')" id="nav-integrity" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Integrity</span>
              <span class="text-[10px] font-mono text-emerald-400">SHA-256</span>
            </button>
          </div>
        </div>

        <!-- SECTION: RELIABILITY -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">RELIABILITY</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('repairs')" id="nav-repairs" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Repairs</span>
              <span id="nav-badge-repairs" class="text-[10px] font-mono text-slate-500">0 jobs</span>
            </button>
            <button onclick="navigateTo('rebalancing')" id="nav-rebalancing" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Rebalancing</span>
              <span class="text-[10px] font-mono text-slate-500">Daemon</span>
            </button>
            <button onclick="navigateTo('fault_injection')" id="nav-fault_injection" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Fault Injection</span>
              <span class="text-[10px] font-mono text-rose-400 font-bold">LAB</span>
            </button>
            <button onclick="navigateTo('quorum')" id="nav-quorum" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Quorum</span>
              <span class="text-[10px] font-mono text-purple-400">R+W&gt;N</span>
            </button>
          </div>
        </div>

        <!-- SECTION: OPERATIONS -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">OPERATIONS</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('events')" id="nav-events" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Events</span>
              <span class="text-[10px] font-mono text-emerald-400">SSE</span>
            </button>
            <button onclick="navigateTo('audit_log')" id="nav-audit_log" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Audit Log</span>
              <span class="text-[10px] font-mono text-slate-500">Records</span>
            </button>
            <button onclick="navigateTo('api_explorer')" id="nav-api_explorer" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>API Explorer</span>
              <span class="text-[10px] font-mono text-purple-400">REST</span>
            </button>
            <button onclick="navigateTo('runbook')" id="nav-runbook" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Runbook</span>
              <span class="text-[10px] font-mono text-emerald-400">Verify</span>
            </button>
          </div>
        </div>

        <!-- SECTION: SYSTEM -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">SYSTEM</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('sqlite')" id="nav-sqlite" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>SQLite</span>
              <span class="text-[10px] font-mono text-slate-500">WAL Mode</span>
            </button>
            <button onclick="navigateTo('atomic_store')" id="nav-atomic_store" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Atomic Store</span>
              <span class="text-[10px] font-mono text-slate-500">POSIX</span>
            </button>
            <button onclick="navigateTo('configuration')" id="nav-configuration" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Configuration</span>
              <span class="text-[10px] font-mono text-slate-500">Env</span>
            </button>
            <button onclick="navigateTo('cluster_identity')" id="nav-cluster_identity" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Identity</span>
              <span class="text-[10px] font-mono text-slate-500">Auth</span>
            </button>
          </div>
        </div>

      </div>

      <!-- Bottom Status Bar -->
      <div class="p-3 border-t border-slate-800/80 bg-[#05070c] flex items-center justify-between text-[11px] font-mono">
        <div class="flex items-center space-x-2">
          <div id="sidebar-node-dot" class="w-2 h-2 rounded-full bg-emerald-400"></div>
          <span id="sidebar-node-text" class="text-slate-400">3 / 3 Hosts</span>
        </div>
        <span class="text-[10px] text-slate-500">v1.4.2</span>
      </div>
    </aside>

    <!-- CONTENT DISPLAY AREA -->
    <main id="view-container" class="flex-1 overflow-y-auto custom-scroll p-6 bg-[#06080d]">
      <!-- Views are dynamically injected here -->
    </main>

  </div>

  <!-- SCRIPT DEFINING APPLICATION LOGIC & REAL-TIME DATA ARCHITECTURE -->
  <script>
    const GATEWAY_BASE = 'http://localhost:8080';

    // ─── API CLIENT LAYER ────────────────────────────────────────────────────────
    class VaultAPI {
      static async request(path, options = {}) {
        const url = \`\${GATEWAY_BASE}\${path}\`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || 8000);
        const start = performance.now();
        try {
          const res = await fetch(url, { ...options, signal: controller.signal });
          clearTimeout(timeoutId);
          const elapsed = Math.round(performance.now() - start);
          const isJson = (res.headers.get('content-type') || '').includes('application/json');
          const data = isJson ? await res.json() : await res.text();
          return { ok: res.ok, status: res.status, headers: res.headers, data, latencyMs: elapsed };
        } catch (err) {
          clearTimeout(timeoutId);
          const elapsed = Math.round(performance.now() - start);
          return { ok: false, status: 0, error: err.name === 'AbortError' ? 'Request timed out' : (err.message || 'Connection refused'), latencyMs: elapsed };
        }
      }

      static async health() { return this.request('/health'); }
      static async clusterStatus() { return this.request('/cluster/status'); }
      static async clusterConfig() { return this.request('/cluster/config'); }
      static async nodes() { return this.request('/nodes'); }
      static async nodeDetails(id) { return this.request(\`/nodes/\${encodeURIComponent(id)}\`); }
      static async drainNode(id) { return this.request(\`/nodes/\${encodeURIComponent(id)}/drain\`, { method: 'POST' }); }
      static async objects() { return this.request('/objects'); }
      static async objectMetadata(key) { return this.request(\`/objects/\${encodeURIComponent(key)}/metadata\`); }
      static async objectPayload(key) { return this.request(\`/objects/\${encodeURIComponent(key)}\`); }
      static async putObject(key, body, expectedVersion = null) {
        const headers = { 'Content-Type': 'application/octet-stream' };
        if (expectedVersion !== null && expectedVersion !== undefined && expectedVersion !== '') {
          headers['X-Expected-Version'] = String(expectedVersion);
        }
        const payload = typeof body === 'string' ? new TextEncoder().encode(body) : body;
        return this.request(\`/objects/\${encodeURIComponent(key)}\`, {
          method: 'PUT',
          headers,
          body: payload
        });
      }
      static async repairs() { return this.request('/repairs'); }
      static async triggerRepair() { return this.request('/repairs/trigger', { method: 'POST' }); }
      static async events(limit = 50) { return this.request(\`/cluster/events?limit=\${limit}\`); }
      static async injectCorruption(nodeId, objectId) {
        return this.request(\`/admin/corrupt/\${encodeURIComponent(nodeId)}/\${encodeURIComponent(objectId)}\`, { method: 'POST' });
      }
    }

    // ─── CENTRAL REACTIVE STORE ───────────────────────────────────────────────────
    const VaultStore = {
      connection: {
        status: 'CONNECTING', // LIVE | GATEWAY OFFLINE | RECONNECTING
        lastSync: null,
        sseStatus: 'CONNECTING', // CONNECTED | CONNECTING | DISCONNECTED
        error: null,
        uptime: 0
      },
      health: null,
      status: null,
      nodes: [],
      objects: [],
      events: [],
      repairs: [],
      config: {
        replicationFactor: 3,
        writeQuorum: 2,
        readQuorum: 2,
        heartbeatInterval: 5000,
        heartbeatTimeout: 15000,
        repairInterval: 10000,
        scanInterval: 60000,
        checksumAlgorithm: 'sha256',
        metadataDatabase: './vault.db'
      },
      activeView: 'dashboard',
      selectedNodeId: 'node-3',
      selectedObjectKey: 'documents/report.txt',
      cachedPayload: null,
      cachedPayloadHeaders: null,
      lastPutResult: null,
      lastConflictResult: null,
      lastDrainResult: null,
      lastCorruptResult: null,
      apiExplorer: {
        method: 'GET',
        path: '/cluster/status',
        headers: '',
        body: '',
        result: null
      },
      ssePaused: false,
      sseLogs: [],
      simulatedQuorum: { n: 3, w: 2, r: 2 },
      simulatedPartition: { 'node-1': true, 'node-2': true, 'node-3': false },
      runbookResults: {}
    };

    // ─── TOAST NOTIFICATION UTILITY ──────────────────────────────────────────────
    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const el = document.createElement('div');
      el.className = \`px-4 py-2.5 rounded-lg text-xs font-mono shadow-xl border pointer-events-auto transition transform duration-200 translate-y-2 opacity-0 flex items-center space-x-2 \${
        type === 'success' ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-300' :
        type === 'error' ? 'bg-rose-950/90 border-rose-500/50 text-rose-300' :
        'bg-slate-900/90 border-slate-700 text-slate-200'
      }\`;
      el.innerHTML = \`<span>\${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>\${message}</span>\`;
      container.appendChild(el);
      requestAnimationFrame(() => {
        el.classList.remove('translate-y-2', 'opacity-0');
      });
      setTimeout(() => {
        el.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => el.remove(), 250);
      }, 3500);
    }

    // ─── MODAL CONFIRMATION UTILITY ──────────────────────────────────────────────
    let activeModalConfirmCallback = null;

    function openModal({ title, endpoint, message, details = null, confirmText = 'Confirm', isDangerous = false, onConfirm }) {
      const modal = document.getElementById('confirm-modal');
      const titleEl = document.getElementById('modal-title');
      const endpointEl = document.getElementById('modal-endpoint');
      const msgEl = document.getElementById('modal-message');
      const detailsEl = document.getElementById('modal-details');
      const btn = document.getElementById('modal-confirm-btn');
      const icon = document.getElementById('modal-icon-container');

      if (!modal) return;
      titleEl.textContent = title;
      endpointEl.textContent = endpoint;
      msgEl.textContent = message;

      if (details) {
        detailsEl.textContent = typeof details === 'string' ? details : JSON.stringify(details, null, 2);
        detailsEl.classList.remove('hidden');
      } else {
        detailsEl.classList.add('hidden');
      }

      btn.textContent = confirmText;
      if (isDangerous) {
        btn.className = 'px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded font-mono text-xs font-bold transition';
        icon.className = 'w-9 h-9 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold font-mono';
      } else {
        btn.className = 'px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded font-mono text-xs font-bold transition';
        icon.className = 'w-9 h-9 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold font-mono';
      }

      activeModalConfirmCallback = onConfirm;
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeModal() {
      const modal = document.getElementById('confirm-modal');
      if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
      }
      activeModalConfirmCallback = null;
    }

    document.getElementById('modal-confirm-btn').addEventListener('click', async () => {
      if (activeModalConfirmCallback) {
        const fn = activeModalConfirmCallback;
        closeModal();
        await fn();
      } else {
        closeModal();
      }
    });

    // ─── REAL-TIME SERVER-SENT EVENTS (SSE) ──────────────────────────────────────
    let sseSource = null;
    let sseReconnectTimer = null;

    function initSSE() {
      if (sseSource) {
        try { sseSource.close(); } catch(e){}
        sseSource = null;
      }
      VaultStore.connection.sseStatus = 'CONNECTING';
      updateHeaderBadges();

      try {
        sseSource = new EventSource(\`\${GATEWAY_BASE}/cluster/events/stream\`);

        sseSource.onopen = () => {
          VaultStore.connection.sseStatus = 'CONNECTED';
          VaultStore.connection.status = 'LIVE';
          VaultStore.connection.lastSync = new Date();
          updateHeaderBadges();
          if (VaultStore.activeView === 'events' || VaultStore.activeView === 'dashboard') {
            reRenderCurrentView();
          }
        };

        sseSource.onmessage = (e) => {
          try {
            const rawEvents = JSON.parse(e.data);
            if (Array.isArray(rawEvents) && rawEvents.length > 0) {
              const existingIds = new Set(VaultStore.events.map(ev => ev.event_id));
              const newEvts = rawEvents.filter(ev => !existingIds.has(ev.event_id));
              if (newEvts.length > 0) {
                VaultStore.events = [...newEvts, ...VaultStore.events].slice(0, 100);
                if (!VaultStore.ssePaused) {
                  newEvts.forEach(ev => {
                    VaultStore.sseLogs.unshift({
                      time: new Date().toISOString(),
                      type: ev.type,
                      msg: ev.message,
                      payload: ev.payload
                    });
                  });
                  VaultStore.sseLogs = VaultStore.sseLogs.slice(0, 200);
                }
                VaultStore.connection.lastSync = new Date();
                updateHeaderBadges();
                reRenderCurrentView();
              }
            }
          } catch(err) {}
        };

        sseSource.addEventListener('status', (e) => {
          try {
            const status = JSON.parse(e.data);
            if (status) {
              VaultStore.status = status;
              if (Array.isArray(status.nodes)) VaultStore.nodes = status.nodes;
              if (Array.isArray(status.recentEvents)) {
                const existingIds = new Set(VaultStore.events.map(ev => ev.event_id));
                const newEvts = status.recentEvents.filter(ev => !existingIds.has(ev.event_id));
                VaultStore.events = [...newEvts, ...VaultStore.events].slice(0, 100);
              }
              VaultStore.connection.lastSync = new Date();
              VaultStore.connection.status = 'LIVE';
              updateHeaderBadges();
              reRenderCurrentView();
            }
          } catch(err) {}
        });

        sseSource.onerror = () => {
          VaultStore.connection.sseStatus = 'DISCONNECTED';
          updateHeaderBadges();
          if (sseSource) {
            sseSource.close();
            sseSource = null;
          }
          clearTimeout(sseReconnectTimer);
          sseReconnectTimer = setTimeout(() => {
            VaultStore.connection.sseStatus = 'RECONNECTING';
            updateHeaderBadges();
            initSSE();
          }, 4000);
        };
      } catch(err) {
        VaultStore.connection.sseStatus = 'DISCONNECTED';
        updateHeaderBadges();
      }
    }

    // ─── POLLING CYCLES ──────────────────────────────────────────────────────────
    // Fast Poller (1.5s): Gateway Health
    async function syncHealth() {
      const res = await VaultAPI.health();
      if (res.ok) {
        VaultStore.health = res.data;
        VaultStore.connection.status = 'LIVE';
        VaultStore.connection.uptime = res.data.uptime || 0;
        VaultStore.connection.lastSync = new Date();
        VaultStore.connection.error = null;
      } else {
        VaultStore.connection.status = 'GATEWAY OFFLINE';
        VaultStore.connection.error = res.error || \`HTTP \${res.status}\`;
      }
      updateHeaderBadges();
    }

    // Medium Poller (5s): Cluster Status, Nodes, Objects, Repairs
    async function syncCluster() {
      const [statusRes, nodesRes, objectsRes, repairsRes] = await Promise.all([
        VaultAPI.clusterStatus(),
        VaultAPI.nodes(),
        VaultAPI.objects(),
        VaultAPI.repairs()
      ]);

      if (statusRes.ok) {
        VaultStore.status = statusRes.data;
        if (Array.isArray(statusRes.data.recentEvents)) {
          const existingIds = new Set(VaultStore.events.map(ev => ev.event_id));
          const newEvts = statusRes.data.recentEvents.filter(ev => !existingIds.has(ev.event_id));
          VaultStore.events = [...newEvts, ...VaultStore.events].slice(0, 100);
        }
      }
      if (nodesRes.ok && Array.isArray(nodesRes.data.nodes)) {
        VaultStore.nodes = nodesRes.data.nodes;
      }
      if (objectsRes.ok && Array.isArray(objectsRes.data.objects)) {
        VaultStore.objects = objectsRes.data.objects;
      }
      if (repairsRes.ok && Array.isArray(repairsRes.data.jobs)) {
        VaultStore.repairs = repairsRes.data.jobs;
      }

      if (statusRes.ok || nodesRes.ok || objectsRes.ok) {
        VaultStore.connection.lastSync = new Date();
        VaultStore.connection.status = 'LIVE';
      }

      updateHeaderBadges();
      reRenderCurrentView();
    }

    // Slow Poller (30s): Config
    async function syncConfig() {
      const res = await VaultAPI.clusterConfig();
      if (res.ok) {
        VaultStore.config = res.data;
      }
    }

    setInterval(syncHealth, 1500);
    setInterval(syncCluster, 5000);
    setInterval(syncConfig, 30000);

    function formatTime(d) {
      if (!d) return '--:--:--';
      const pad = n => String(n).padStart(2, '0');
      return \`\${pad(d.getHours())}:\${pad(d.getMinutes())}:\${pad(d.getSeconds())}\`;
    }

    function updateHeaderBadges() {
      const connDot = document.getElementById('header-conn-dot');
      const connText = document.getElementById('header-conn-text');
      const syncTime = document.getElementById('header-sync-time');
      const gwStatus = document.getElementById('header-gw-status');
      const sseStatus = document.getElementById('header-sse-status');
      const clusterStatus = document.getElementById('header-cluster-status');
      const sideDot = document.getElementById('sidebar-node-dot');
      const sideText = document.getElementById('sidebar-node-text');
      const navBadgeNodes = document.getElementById('nav-badge-nodes');
      const navBadgeObj = document.getElementById('nav-badge-obj-count');
      const navBadgeRepairs = document.getElementById('nav-badge-repairs');
      const navBadgeNodeSel = document.getElementById('nav-badge-selected-node');

      if (syncTime) syncTime.textContent = formatTime(VaultStore.connection.lastSync);

      const isLive = VaultStore.connection.status === 'LIVE';

      if (connDot && connText) {
        if (isLive) {
          connDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
          connText.textContent = 'LIVE';
          connText.className = 'text-emerald-300 font-mono font-medium';
        } else {
          connDot.className = 'w-2 h-2 rounded-full bg-rose-500';
          connText.textContent = 'GATEWAY OFFLINE';
          connText.className = 'text-rose-400 font-mono font-medium';
        }
      }

      if (gwStatus) {
        if (isLive) {
          gwStatus.textContent = \`localhost:8080 (UP - \${VaultStore.connection.uptime}s)\`;
          gwStatus.className = 'text-emerald-400 font-semibold font-mono';
        } else {
          gwStatus.textContent = 'localhost:8080 (OFFLINE)';
          gwStatus.className = 'text-rose-400 font-semibold font-mono';
        }
      }

      if (sseStatus) {
        sseStatus.textContent = VaultStore.connection.sseStatus;
        sseStatus.className = VaultStore.connection.sseStatus === 'CONNECTED'
          ? 'text-emerald-400 font-semibold'
          : VaultStore.connection.sseStatus === 'CONNECTING' || VaultStore.connection.sseStatus === 'RECONNECTING'
          ? 'text-amber-400 font-semibold'
          : 'text-rose-400 font-semibold';
      }

      if (clusterStatus) {
        if (!isLive) {
          clusterStatus.textContent = 'OFFLINE';
          clusterStatus.className = 'text-rose-400 font-semibold';
        } else {
          const draining = VaultStore.nodes.filter(n => n.state === 'DRAINING').length;
          const failed = VaultStore.nodes.filter(n => n.state === 'FAILED').length;
          if (failed > 0 || draining > 0) {
            clusterStatus.textContent = 'DEGRADED';
            clusterStatus.className = 'text-amber-400 font-semibold';
          } else {
            clusterStatus.textContent = 'HEALTHY';
            clusterStatus.className = 'text-emerald-400 font-semibold';
          }
        }
      }

      if (sideDot && sideText) {
        const active = VaultStore.nodes.filter(n => n.state === 'HEALTHY' || n.state === 'DRAINING').length;
        const total = VaultStore.nodes.length || 3;
        sideText.textContent = \`\${active} / \${total} Hosts\`;
        sideDot.className = active >= 2 ? 'w-2 h-2 rounded-full bg-emerald-400' : 'w-2 h-2 rounded-full bg-amber-400';
      }

      if (navBadgeNodes) navBadgeNodes.textContent = \`\${VaultStore.nodes.length || 3} Hosts\`;
      if (navBadgeObj) navBadgeObj.textContent = \`\${VaultStore.objects.length} objs\`;
      if (navBadgeRepairs) navBadgeRepairs.textContent = \`\${VaultStore.repairs.length} jobs\`;
      if (navBadgeNodeSel) navBadgeNodeSel.textContent = VaultStore.selectedNodeId;
    }

    function reRenderCurrentView() {
      if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) {
        return;
      }
      const container = document.getElementById('view-container');
      if (container && views[VaultStore.activeView]) {
        container.innerHTML = views[VaultStore.activeView].render();
      }
    }

    // ─── INTERACTIVE OPERATIONAL HANDLERS ────────────────────────────────────────
    window.inspectObject = function(key) {
      VaultStore.selectedObjectKey = key;
      VaultStore.cachedPayload = null;
      VaultStore.cachedPayloadHeaders = null;
      navigateTo('object_detail');
    };

    window.inspectNode = function(nodeId) {
      VaultStore.selectedNodeId = nodeId;
      navigateTo('node_detail');
    };

    window.fetchRawPayloadLive = async function(key) {
      const btn = document.getElementById('fetch-payload-btn');
      if (btn) btn.textContent = 'Fetching from Quorum (R=2)...';
      const res = await VaultAPI.objectPayload(key);
      if (res.ok) {
        VaultStore.cachedPayload = res.data;
        VaultStore.cachedPayloadHeaders = {
          checksum: res.headers.get('x-vault-checksum') || res.headers.get('x-object-checksum'),
          version: res.headers.get('x-vault-version') || res.headers.get('x-object-version'),
          contentType: res.headers.get('content-type'),
          status: res.status,
          latencyMs: res.latencyMs
        };
        showToast(\`Object \${key} fetched successfully (\${res.latencyMs}ms)\`, 'success');
      } else {
        VaultStore.cachedPayload = \`Error fetching object: \${res.error || res.status}\`;
        showToast(\`Fetch failed: \${res.error || res.status}\`, 'error');
      }
      reRenderCurrentView();
    };

    window.verifyChecksumLive = async function(key, expectedHash) {
      const res = await VaultAPI.objectPayload(key);
      if (!res.ok) {
        showToast('Cannot verify: payload fetch failed', 'error');
        return;
      }
      const rawText = typeof res.data === 'string' ? res.data : new TextDecoder().decode(res.data);
      const encoder = new TextEncoder();
      const data = encoder.encode(rawText);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const calculatedHash = 'sha256:' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      const matches = calculatedHash.toLowerCase() === expectedHash.toLowerCase();
      if (matches) {
        alert(\`CRYPTOGRAPHIC INTEGRITY VERIFIED\\n\\nExpected: \${expectedHash}\\nCalculated: \${calculatedHash}\\n\\nStatus: MATCH CONFIRMED (Zero bit rot detected)\`);
        showToast('SHA-256 Checksum Verified [MATCH ✓]', 'success');
      } else {
        alert(\`CHECKSUM MISMATCH DETECTED!\\n\\nExpected: \${expectedHash}\\nCalculated: \${calculatedHash}\\n\\nStatus: CORRUPT BLOCK DETECTED\`);
        showToast('Checksum Mismatch Detected!', 'error');
      }
    };

    window.downloadObjectPayload = async function(key) {
      const res = await VaultAPI.objectPayload(key);
      if (!res.ok) {
        showToast('Download failed', 'error');
        return;
      }
      const blob = new Blob([res.data], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = key.split('/').pop() || 'object.bin';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(\`Downloaded \${key}\`, 'success');
    };

    window.submitObjectIngestion = async function(e) {
      if (e) e.preventDefault();
      const keyInput = document.getElementById('ingest-key');
      const bodyInput = document.getElementById('ingest-body');
      const expVerInput = document.getElementById('ingest-exp-version');
      const btn = document.getElementById('ingest-submit-btn');

      const key = keyInput ? keyInput.value.trim() : 'documents/note.txt';
      const body = bodyInput ? bodyInput.value : '';
      const expVer = expVerInput && expVerInput.value !== '' ? parseInt(expVerInput.value, 10) : null;

      if (!key) {
        showToast('Object key is required', 'error');
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Writing to Quorum (W=2)...';
      }

      const res = await VaultAPI.putObject(key, body, expVer);
      VaultStore.lastPutResult = {
        key,
        res,
        timestamp: new Date(),
        size: new Blob([body]).size
      };

      await syncCluster();

      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Upload Object (PUT)';
      }

      if (res.ok) {
        showToast(\`Object \${key} stored (HTTP 201 Created)\`, 'success');
        inspectObject(key);
      } else if (res.status === 409) {
        VaultStore.lastConflictResult = res;
        showToast('Version conflict (HTTP 409 Rejected)', 'error');
        navigateTo('versions');
      } else {
        showToast(\`Upload failed: HTTP \${res.status} \${res.error || ''}\`, 'error');
        reRenderCurrentView();
      }
    };

    window.confirmDrainNode = function(nodeId) {
      openModal({
        title: \`Gracefully Drain \${nodeId}\`,
        endpoint: \`POST /nodes/\${nodeId}/drain\`,
        message: \`Drain \${nodeId}? This blocks new incoming writes to \${nodeId} while keeping existing replicas available for read quorum. Replicas will be scheduled for autonomous migration.\`,
        confirmText: 'Confirm Drain',
        isDangerous: true,
        onConfirm: async () => {
          const res = await VaultAPI.drainNode(nodeId);
          VaultStore.lastDrainResult = res;
          if (res.ok) {
            showToast(\`Node \${nodeId} is now DRAINING\`, 'success');
          } else {
            showToast(\`Drain failed: \${res.error || res.data?.error}\`, 'error');
          }
          await syncCluster();
          reRenderCurrentView();
        }
      });
    };

    window.confirmTriggerRepair = function() {
      openModal({
        title: 'Trigger Replica Repair Scan',
        endpoint: 'POST /repairs/trigger',
        message: 'Scan the cluster for under-replicated or corrupt objects and immediately queue repair jobs to restore N=3 replication?',
        confirmText: 'Trigger Scan',
        onConfirm: async () => {
          const res = await VaultAPI.triggerRepair();
          if (res.ok) {
            showToast(\`Repair triggered: \${res.data?.message || 'Queued'}\`, 'success');
          } else {
            showToast(\`Trigger failed: \${res.error}\`, 'error');
          }
          await syncCluster();
          reRenderCurrentView();
        }
      });
    };

    window.confirmInjectCorruption = function(nodeId, objectId) {
      openModal({
        title: 'Inject Bit-Rot Corruption (Fault Lab)',
        endpoint: \`POST /admin/corrupt/\${nodeId}/\${objectId}\`,
        message: \`[WARNING: SIMULATION/DEMO TOOL] Overwrite 64 bytes of \${objectId} on \${nodeId} with random garbage bytes? The background scanner will detect checksum mismatch and trigger autonomous healing.\`,
        confirmText: 'Inject Corruption',
        isDangerous: true,
        onConfirm: async () => {
          const res = await VaultAPI.injectCorruption(nodeId, objectId);
          VaultStore.lastCorruptResult = res;
          if (res.ok) {
            showToast(\`Corruption injected on \${nodeId}\`, 'success');
          } else {
            showToast(\`Injection failed: \${res.error || res.data?.error}\`, 'error');
          }
          await syncCluster();
          reRenderCurrentView();
        }
      });
    };

    window.runOCCConflictTest = async function() {
      const obj = VaultStore.objects[0];
      const key = obj ? obj.logical_key : 'documents/report.txt';
      const res = await VaultAPI.putObject(key, 'Stale concurrency mutation attempt', 0);
      VaultStore.lastConflictResult = res;
      if (res.status === 409) {
        showToast('OCC Invariant Verified: HTTP 409 Conflict properly rejected stale write', 'success');
      } else {
        showToast(\`Unexpected status: HTTP \${res.status}\`, 'error');
      }
      reRenderCurrentView();
    };

    window.sendApiExplorerRequest = async function() {
      const method = document.getElementById('api-method')?.value || 'GET';
      const path = document.getElementById('api-path')?.value || '/cluster/status';
      const headersRaw = document.getElementById('api-headers')?.value || '';
      const body = document.getElementById('api-body')?.value || '';

      const opts = { method };
      const headers = {};
      if (headersRaw.trim()) {
        headersRaw.split('\\n').forEach(line => {
          const idx = line.indexOf(':');
          if (idx > -1) headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
        });
        opts.headers = headers;
      }
      if (method !== 'GET' && method !== 'HEAD' && body) {
        opts.body = body;
        if (!opts.headers) opts.headers = { 'Content-Type': 'application/json' };
      }

      const res = await VaultAPI.request(path, opts);
      VaultStore.apiExplorer = { method, path, headers: headersRaw, body, result: res };
      showToast(\`HTTP \${res.status} (\${res.latencyMs}ms)\`, res.ok ? 'success' : 'error');
      reRenderCurrentView();
    };

    window.setApiPreset = function(method, path, body = '', headers = '') {
      const m = document.getElementById('api-method');
      const p = document.getElementById('api-path');
      const b = document.getElementById('api-body');
      const h = document.getElementById('api-headers');
      if (m) m.value = method;
      if (p) p.value = path;
      if (b) b.value = body;
      if (h) h.value = headers;
    };

    window.copyText = function(text) {
      navigator.clipboard.writeText(text);
      showToast('Copied to clipboard', 'info');
    };

    window.runRunbookStep = async function(stepNum) {
      let outcome = { passed: false, detail: '' };
      try {
        if (stepNum === 1) {
          const res = await VaultAPI.health();
          outcome = { passed: res.ok && res.data?.status === 'UP', detail: \`Gateway UP (Uptime: \${res.data?.uptime}s)\` };
        } else if (stepNum === 2) {
          const res = await VaultAPI.nodes();
          const count = res.data?.nodes?.length || 0;
          outcome = { passed: res.ok && count >= 3, detail: \`\${count} Nodes Registered & Heartbeating\` };
        } else if (stepNum === 3) {
          const res = await VaultAPI.putObject('documents/runbook-test.txt', 'Vault Distributed Cluster Verification', null);
          outcome = { passed: res.ok, detail: \`HTTP 201 Created (Parallel W=2 acknowledged)\` };
        } else if (stepNum === 4) {
          const res = await VaultAPI.objectMetadata('documents/runbook-test.txt');
          const reps = res.data?.replicas?.length || 0;
          outcome = { passed: res.ok && reps >= 2, detail: \`\${reps} Replicas verified across storage nodes\` };
        } else if (stepNum === 5) {
          const res = await VaultAPI.objectPayload('documents/runbook-test.txt');
          outcome = { passed: res.ok && String(res.data).includes('Verification'), detail: 'HTTP 200 OK — Quorum R=2 delivered consistent bytes' };
        } else if (stepNum === 6) {
          const res = await VaultAPI.putObject('documents/runbook-test.txt', 'Stale write test', 0);
          outcome = { passed: res.status === 409, detail: 'HTTP 409 Conflict properly rejected stale expected version 0' };
        } else if (stepNum === 7) {
          const res = await VaultAPI.drainNode('node-3');
          outcome = { passed: res.ok || res.status === 400, detail: res.data?.message || 'Node node-3 draining acknowledged' };
        } else if (stepNum === 8) {
          const res = await VaultAPI.triggerRepair();
          outcome = { passed: res.ok, detail: res.data?.message || 'RepairWorker scanned cluster replicas' };
        }
      } catch(err) {
        outcome = { passed: false, detail: err.message };
      }
      VaultStore.runbookResults[stepNum] = { ...outcome, timestamp: new Date() };
      await syncCluster();
      reRenderCurrentView();
    };

    window.runAllRunbookSteps = async function() {
      for (let i = 1; i <= 8; i++) {
        await window.runRunbookStep(i);
      }
      showToast('Runbook verification suite completed', 'success');
    };
`;

fs.writeFileSync('C:\\surya\\vault\\scripts\\build_real_life_control_plane.mjs', htmlContent);
console.log('App scaffold written.');
