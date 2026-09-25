"""
scripts/app_js.py
Contains the JavaScript core runtime and API layer for Vault Control Plane.
"""

def get_js_runtime():
    return r"""
  <script>
    const GATEWAY_BASE = 'http://localhost:8080';

    // ─── API CLIENT LAYER ────────────────────────────────────────────────────────
    class VaultAPI {
      static async request(path, options = {}) {
        const url = `${GATEWAY_BASE}${path}`;
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
      static async nodeDetails(id) { return this.request(`/nodes/${encodeURIComponent(id)}`); }
      static async drainNode(id) { return this.request(`/nodes/${encodeURIComponent(id)}/drain`, { method: 'POST' }); }
      static async objects() { return this.request('/objects'); }
      static async objectMetadata(key) { return this.request(`/objects/${encodeURIComponent(key)}/metadata`); }
      static async objectPayload(key) { return this.request(`/objects/${encodeURIComponent(key)}`); }
      static async putObject(key, body, expectedVersion = null) {
        const headers = { 'Content-Type': 'application/octet-stream' };
        if (expectedVersion !== null && expectedVersion !== undefined && expectedVersion !== '') {
          headers['X-Expected-Version'] = String(expectedVersion);
        }
        let payload = body;
        if (typeof body === 'string') {
          payload = new TextEncoder().encode(body);
        }
        return this.request(`/objects/${encodeURIComponent(key)}`, {
          method: 'PUT',
          headers,
          body: payload
        });
      }
      static async deleteObject(key) {
        return this.request(`/objects/${encodeURIComponent(key)}`, { method: 'DELETE' });
      }
      static async repairs() { return this.request('/repairs'); }
      static async triggerRepair() { return this.request('/repairs/trigger', { method: 'POST' }); }
      static async events(limit = 50) { return this.request(`/cluster/events?limit=${limit}`); }
      static async injectCorruption(nodeId, objectId) {
        return this.request(`/admin/corrupt/${encodeURIComponent(nodeId)}/${encodeURIComponent(objectId)}`, { method: 'POST' });
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
      activeView: 'presentation',
      selectedNodeId: 'node-3',
      selectedObjectKey: 'documents/report.txt',
      cachedPayload: null,
      cachedPayloadHeaders: null,
      lastPutResult: null,
      occConflictResult: null,
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
      quorumCalc: { n: 3, r: 2, w: 2 },
      demoResults: [
        { step: 1, name: 'Check Gateway', expected: 'Gateway Connected & Uptime Verified', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 2, name: 'Check Nodes', expected: 'Inspect Registered Nodes & States', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 3, name: 'List Objects', expected: 'Retrieve Live Object Catalog', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 4, name: 'Read Object', expected: 'Fetch Live Payload via Quorum R=2', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 5, name: 'Write Object', expected: 'Ingest Object with Strict W=2 Quorum', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 6, name: 'Verify Version', expected: 'Stale Expected-Version Rejection (409)', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 7, name: 'Verify Integrity', expected: 'Validate Cryptographic SHA-256 Digest', status: 'IDLE', detail: '', latencyMs: 0 },
        { step: 8, name: 'Watch Events', expected: 'Confirm Real-Time SSE Event Stream', status: 'IDLE', detail: '', latencyMs: 0 }
      ]
    };

    // ─── TOAST NOTIFICATION UTILITY ──────────────────────────────────────────────
    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const el = document.createElement('div');
      el.className = `px-4 py-2.5 rounded-lg text-xs font-mono shadow-xl border pointer-events-auto transition transform duration-200 translate-y-2 opacity-0 flex items-center space-x-2 ${
        type === 'success' ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-300' :
        type === 'error' ? 'bg-rose-950/90 border-rose-500/50 text-rose-300' :
        'bg-slate-900/90 border-slate-700 text-slate-200'
      }`;
      el.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>${message}</span>`;
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

    document.getElementById('modal-confirm-btn')?.addEventListener('click', async () => {
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
        sseSource = new EventSource(`${GATEWAY_BASE}/cluster/events/stream`);

        sseSource.onopen = () => {
          VaultStore.connection.sseStatus = 'CONNECTED';
          VaultStore.connection.status = 'LIVE';
          VaultStore.connection.lastSync = new Date();
          updateHeaderBadges();
          if (VaultStore.activeView === 'events' || VaultStore.activeView === 'dashboard' || VaultStore.activeView === 'demo_mode') {
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
                      time: new Date().toLocaleTimeString(),
                      type: ev.type,
                      msg: ev.message,
                      node: ev.node_id || 'gateway',
                      object: ev.object_id || 'N/A',
                      status: 'OK',
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
        VaultStore.connection.error = res.error || `HTTP ${res.status}`;
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
      return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }

    function updateHeaderBadges() {
      const connDot = document.getElementById('header-conn-dot');
      const connText = document.getElementById('header-conn-text');
      const syncTime = document.getElementById('header-sync-time');
      const sseStatus = document.getElementById('header-sse-status');
      const sseDot = document.getElementById('header-sse-dot');
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
          connText.textContent = '● GATEWAY CONNECTED';
          connText.className = 'text-emerald-300 font-mono font-medium';
        } else {
          connDot.className = 'w-2 h-2 rounded-full bg-rose-500';
          connText.textContent = '● GATEWAY OFFLINE';
          connText.className = 'text-rose-400 font-mono font-medium';
        }
      }

      if (sseStatus && sseDot) {
        if (VaultStore.connection.sseStatus === 'CONNECTED') {
          sseDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
          sseStatus.textContent = '● SSE CONNECTED';
          sseStatus.className = 'text-emerald-400 font-semibold font-mono';
        } else if (VaultStore.connection.sseStatus === 'CONNECTING' || VaultStore.connection.sseStatus === 'RECONNECTING') {
          sseDot.className = 'w-2 h-2 rounded-full bg-amber-400 animate-ping';
          sseStatus.textContent = '● SSE CONNECTING';
          sseStatus.className = 'text-amber-400 font-semibold font-mono';
        } else {
          sseDot.className = 'w-2 h-2 rounded-full bg-rose-500';
          sseStatus.textContent = '● SSE OFFLINE';
          sseStatus.className = 'text-rose-400 font-semibold font-mono';
        }
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
        sideText.textContent = `${active} / ${total} Hosts`;
        sideDot.className = active >= 2 ? 'w-2 h-2 rounded-full bg-emerald-400' : 'w-2 h-2 rounded-full bg-amber-400';
      }

      if (navBadgeNodes) navBadgeNodes.textContent = `${VaultStore.nodes.length || 3} Hosts`;
      if (navBadgeObj) navBadgeObj.textContent = `${VaultStore.objects.length} objs`;
      if (navBadgeRepairs) navBadgeRepairs.textContent = `${VaultStore.repairs.length} jobs`;
      if (navBadgeNodeSel) navBadgeNodeSel.textContent = VaultStore.selectedNodeId;
    }

    function reRenderCurrentView() {
      if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) {
        return;
      }
      const container = document.getElementById('view-container');
      if (container && window.views && window.views[VaultStore.activeView]) {
        container.innerHTML = window.views[VaultStore.activeView].render();
      }
    }

    // ─── OPERATIONAL & DEMO ACTION HANDLERS ──────────────────────────────────────
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

    window.fetchObjectPayload = async function(key) {
      showToast(`Fetching ${key} via Quorum R=2...`, 'info');
      const res = await VaultAPI.objectPayload(key);
      if (res.ok) {
        VaultStore.cachedPayload = res.data;
        VaultStore.cachedPayloadHeaders = {
          checksum: res.headers.get('x-vault-checksum') || res.headers.get('x-object-checksum'),
          version: res.headers.get('x-vault-version') || res.headers.get('x-object-version'),
          objectId: res.headers.get('x-object-id'),
          contentType: res.headers.get('content-type'),
          status: res.status,
          latencyMs: res.latencyMs
        };
        showToast(`Object fetched in ${res.latencyMs}ms [HTTP 200 OK]`, 'success');
      } else {
        VaultStore.cachedPayload = `Error fetching object: ${res.error || res.status}`;
        showToast(`Fetch failed: ${res.error || res.status}`, 'error');
      }
      reRenderCurrentView();
    };

    window.verifyObjectChecksum = async function(key, expectedHash) {
      const res = await VaultAPI.objectPayload(key);
      if (!res.ok) {
        showToast('Fetch failed: cannot verify checksum', 'error');
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
        alert(`CRYPTOGRAPHIC INTEGRITY CONFIRMED\n\nObject Key: ${key}\nExpected Digest: ${expectedHash}\nCalculated Digest: ${calculatedHash}\n\nStatus: MATCH (0 bit rot detected)`);
        showToast('SHA-256 Verified [MATCH ✓]', 'success');
      } else {
        alert(`INTEGRITY MISMATCH DETECTED!\n\nObject Key: ${key}\nExpected: ${expectedHash}\nCalculated: ${calculatedHash}\n\nStatus: MISMATCH (Corrupted block)`);
        showToast('Integrity Mismatch Detected!', 'error');
      }
    };

    window.viewRawPayload = function(key) {
      if (!VaultStore.cachedPayload) {
        window.fetchObjectPayload(key);
      } else {
        const raw = typeof VaultStore.cachedPayload === 'string' ? VaultStore.cachedPayload : JSON.stringify(VaultStore.cachedPayload, null, 2);
        alert(`RAW OBJECT BYTES (${key}):\n\n${raw}`);
      }
    };

    window.submitObjectUpload = async function(e) {
      if (e) e.preventDefault();
      const keyInput = document.getElementById('upload-key');
      const textInput = document.getElementById('upload-text-payload');
      const fileInput = document.getElementById('upload-file-input');
      const expVerInput = document.getElementById('upload-exp-version');
      const btn = document.getElementById('upload-submit-btn');

      const key = keyInput ? keyInput.value.trim() : 'documents/demo.txt';
      const expVer = expVerInput && expVerInput.value !== '' ? parseInt(expVerInput.value, 10) : null;

      if (!key) {
        showToast('Object key is required', 'error');
        return;
      }

      let payloadData = '';
      if (fileInput && fileInput.files && fileInput.files.length > 0) {
        payloadData = await fileInput.files[0].arrayBuffer();
      } else if (textInput) {
        payloadData = textInput.value;
      }

      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Writing to Quorum (W=2)...';
      }

      const res = await VaultAPI.putObject(key, payloadData, expVer);
      const byteSize = typeof payloadData === 'string' ? new Blob([payloadData]).size : payloadData.byteLength || 0;

      VaultStore.lastPutResult = {
        key,
        res,
        status: res.status,
        timestamp: new Date(),
        size: byteSize,
        data: res.data
      };

      await syncCluster();

      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Upload Object (PUT)';
      }

      if (res.ok) {
        showToast(`Object ${key} created successfully [HTTP ${res.status}]`, 'success');
        inspectObject(key);
      } else if (res.status === 409) {
        VaultStore.occConflictResult = res;
        showToast('Stale write rejected: HTTP 409 Conflict', 'error');
        navigateTo('versions');
      } else {
        showToast(`Upload failed: HTTP ${res.status} ${res.error || ''}`, 'error');
        reRenderCurrentView();
      }
    };

    window.testVersionConflict = async function() {
      const obj = VaultStore.objects[0];
      const key = obj ? obj.logical_key : 'documents/report.txt';
      showToast(`Testing OCC conflict on ${key} with stale version 0...`, 'info');
      const res = await VaultAPI.putObject(key, 'Stale concurrent update attempt', 0);
      VaultStore.occConflictResult = res;
      if (res.status === 409) {
        showToast('VERSION CONFLICT VERIFIED [HTTP 409 Rejection]', 'success');
      } else {
        showToast(`Unexpected status: HTTP ${res.status}`, 'error');
      }
      reRenderCurrentView();
    };

    window.confirmDrainNode = function(nodeId) {
      openModal({
        title: `DRAIN ${nodeId}?`,
        endpoint: `POST /nodes/${nodeId}/drain`,
        message: `Drain node ${nodeId}? This will change the node state to DRAINING and block new incoming writes while keeping existing replicas available for read quorum.`,
        confirmText: 'Confirm Drain',
        isDangerous: true,
        onConfirm: async () => {
          const res = await VaultAPI.drainNode(nodeId);
          VaultStore.lastDrainResult = res;
          if (res.ok) {
            showToast(`Node ${nodeId} state set to DRAINING`, 'success');
          } else {
            showToast(`Drain failed: ${res.error || res.data?.error}`, 'error');
          }
          await syncCluster();
          reRenderCurrentView();
        }
      });
    };

    window.confirmInjectCorruption = function(nodeId, objectId) {
      openModal({
        title: 'Inject Bit-Rot Corruption (Fault Lab)',
        endpoint: `POST /admin/corrupt/${nodeId}/${objectId}`,
        message: `[SIMULATION ONLY] Overwrite 64 random bytes in ${objectId} on ${nodeId}? The background integrity scanner will detect checksum mismatch and queue an autonomous repair.`,
        confirmText: 'Inject Corruption',
        isDangerous: true,
        onConfirm: async () => {
          const res = await VaultAPI.injectCorruption(nodeId, objectId);
          VaultStore.lastCorruptResult = res;
          if (res.ok) {
            showToast(`Bit-rot corruption injected into ${nodeId}`, 'success');
          } else {
            showToast(`Injection failed: ${res.error || res.data?.error}`, 'error');
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
        message: 'Scan the storage cluster for missing, under-replicated, or corrupted replicas and trigger autonomous RepairWorker healing?',
        confirmText: 'Trigger Scan',
        onConfirm: async () => {
          const res = await VaultAPI.triggerRepair();
          if (res.ok) {
            showToast(`Repair scan initiated: ${res.data?.message || 'Queued'}`, 'success');
          } else {
            showToast(`Scan trigger failed: ${res.error}`, 'error');
          }
          await syncCluster();
          reRenderCurrentView();
        }
      });
    };

    window.updateQuorumCalc = function() {
      const nInput = document.getElementById('calc-n');
      const rInput = document.getElementById('calc-r');
      const wInput = document.getElementById('calc-w');
      if (nInput && rInput && wInput) {
        VaultStore.quorumCalc = {
          n: parseInt(nInput.value, 10) || 3,
          r: parseInt(rInput.value, 10) || 2,
          w: parseInt(wInput.value, 10) || 2
        };
        reRenderCurrentView();
      }
    };

    // ─── 8-STEP GUIDED DEMONSTRATION RUNNER ─────────────────────────────────────────
    window.runDemoStep = async function(stepNum) {
      const stepIndex = stepNum - 1;
      const step = VaultStore.demoResults[stepIndex];
      step.status = 'RUNNING';
      reRenderCurrentView();

      const start = performance.now();
      try {
        if (stepNum === 1) {
          const res = await VaultAPI.health();
          step.latencyMs = Math.round(performance.now() - start);
          if (res.ok && res.data?.status === 'UP') {
            step.status = 'PASS';
            step.detail = `Gateway Connected & UP (Uptime: ${res.data?.uptime}s)`;
          } else {
            step.status = 'FAIL';
            step.detail = res.error || `HTTP ${res.status}`;
          }
        } else if (stepNum === 2) {
          const res = await VaultAPI.nodes();
          step.latencyMs = Math.round(performance.now() - start);
          const nodes = res.data?.nodes || [];
          if (res.ok && nodes.length >= 3) {
            step.status = 'PASS';
            step.detail = `${nodes.length} Storage Nodes Discovered (${nodes.map(n => n.node_id + ':' + n.state).join(', ')})`;
          } else {
            step.status = 'FAIL';
            step.detail = res.error || `Only ${nodes.length} nodes found`;
          }
        } else if (stepNum === 3) {
          const res = await VaultAPI.objects();
          step.latencyMs = Math.round(performance.now() - start);
          const objs = res.data?.objects || [];
          if (res.ok && objs.length > 0) {
            step.status = 'PASS';
            step.detail = `Discovered ${objs.length} Real Objects (${objs.map(o => o.logical_key).slice(0, 3).join(', ')}...)`;
          } else {
            step.status = 'FAIL';
            step.detail = res.error || 'No objects found';
          }
        } else if (stepNum === 4) {
          const targetKey = VaultStore.objects[0]?.logical_key || 'documents/report.txt';
          const res = await VaultAPI.objectPayload(targetKey);
          step.latencyMs = Math.round(performance.now() - start);
          if (res.ok) {
            step.status = 'PASS';
            step.detail = `Read ${targetKey} [HTTP 200 OK] — Delivered from Quorum R=2 (${res.latencyMs}ms)`;
          } else {
            step.status = 'FAIL';
            step.detail = res.error || `HTTP ${res.status}`;
          }
        } else if (stepNum === 5) {
          const writeKey = 'documents/hackathon-demo-proof.txt';
          const payload = 'Vault Live Verification Payload — Written via Parallel W=2 Quorum';
          const res = await VaultAPI.putObject(writeKey, payload, null);
          step.latencyMs = Math.round(performance.now() - start);
          if (res.ok) {
            step.status = 'PASS';
            step.detail = `Ingested ${writeKey} [HTTP 201 Created] (Version: ${res.data?.version}, Checksum: ${res.data?.checksum?.substring(0, 16)}...)`;
          } else {
            step.status = 'FAIL';
            step.detail = res.error || `HTTP ${res.status}`;
          }
        } else if (stepNum === 6) {
          const targetKey = VaultStore.objects[0]?.logical_key || 'documents/report.txt';
          const res = await VaultAPI.putObject(targetKey, 'Stale concurrent write', 0);
          step.latencyMs = Math.round(performance.now() - start);
          if (res.status === 409) {
            step.status = 'PASS';
            step.detail = `Stale Expected-Version: 0 safely rejected [HTTP 409 Conflict] — Invariant SI-03 Enforced`;
          } else {
            step.status = 'FAIL';
            step.detail = `Expected HTTP 409, received HTTP ${res.status}`;
          }
        } else if (stepNum === 7) {
          const targetKey = VaultStore.objects[0]?.logical_key || 'documents/report.txt';
          const metaRes = await VaultAPI.objectMetadata(targetKey);
          const payRes = await VaultAPI.objectPayload(targetKey);
          step.latencyMs = Math.round(performance.now() - start);
          if (metaRes.ok && payRes.ok) {
            const rawText = typeof payRes.data === 'string' ? payRes.data : new TextDecoder().decode(payRes.data);
            const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(rawText));
            const calculated = 'sha256:' + Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
            const expected = metaRes.data?.checksum || '';
            if (calculated.toLowerCase() === expected.toLowerCase()) {
              step.status = 'PASS';
              step.detail = `Calculated SHA-256 MATCHES Metadata Checksum (${expected.substring(0, 20)}...) — 0 Bit Rot`;
            } else {
              step.status = 'FAIL';
              step.detail = `Checksum MISMATCH! Expected ${expected}, calculated ${calculated}`;
            }
          } else {
            step.status = 'FAIL';
            step.detail = 'Failed to fetch object for checksum verification';
          }
        } else if (stepNum === 8) {
          step.latencyMs = 0;
          if (VaultStore.connection.sseStatus === 'CONNECTED') {
            step.status = 'PASS';
            step.detail = `EventSource Active at /cluster/events/stream — ${VaultStore.events.length} Live Events Captured`;
          } else {
            step.status = 'NOT AVAILABLE';
            step.detail = `SSE Stream status is ${VaultStore.connection.sseStatus}`;
          }
        }
      } catch (err) {
        step.status = 'FAIL';
        step.detail = err.message || 'Execution error';
      }

      await syncCluster();
      reRenderCurrentView();
    };

    window.runCompleteDemo = async function() {
      showToast('Starting complete 8-step demonstration...', 'info');
      for (let i = 1; i <= 8; i++) {
        await window.runDemoStep(i);
        await new Promise(r => setTimeout(r, 600));
      }
      showToast('Complete demonstration workflow finished!', 'success');
    };

    // ─── API EXPLORER ─────────────────────────────────────────────────────────────
    window.sendApiExplorerRequest = async function() {
      const method = document.getElementById('api-method')?.value || 'GET';
      const path = document.getElementById('api-path')?.value || '/cluster/status';
      const headersRaw = document.getElementById('api-headers')?.value || '';
      const body = document.getElementById('api-body')?.value || '';

      const opts = { method };
      const headers = {};
      if (headersRaw.trim()) {
        headersRaw.split('\n').forEach(line => {
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
      showToast(`HTTP ${res.status} (${res.latencyMs}ms)`, res.ok ? 'success' : 'error');
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

    window.toggleSsePause = function() {
      VaultStore.ssePaused = !VaultStore.ssePaused;
      showToast(VaultStore.ssePaused ? 'SSE logs paused' : 'SSE logs resumed', 'info');
      reRenderCurrentView();
    };

    window.clearSse = function() {
      VaultStore.sseLogs = [];
      showToast('SSE terminal logs cleared', 'info');
      reRenderCurrentView();
    };

    window.reconnectSse = function() {
      initSSE();
      showToast('Reconnecting SSE stream...', 'info');
    };

    // ─── ROUTER & VIEW NAVIGATION ────────────────────────────────────────────────
    window.navigateTo = function(viewId) {
      if (!window.views || !window.views[viewId]) {
        console.warn('View not found:', viewId);
        viewId = 'presentation';
      }
      VaultStore.activeView = viewId;

      document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      const activeNav = document.getElementById(`nav-${viewId}`);
      if (activeNav) activeNav.classList.add('active');

      const view = window.views[viewId];
      const secEl = document.getElementById('breadcrumb-section');
      const pageEl = document.getElementById('breadcrumb-page');
      if (secEl) secEl.textContent = view.section;
      if (pageEl) pageEl.textContent = view.title;

      const sel = document.getElementById('quick-jump-select');
      if (sel) sel.value = viewId;

      const container = document.getElementById('view-container');
      if (container) {
        container.innerHTML = view.render();
        container.scrollTop = 0;
      }
    };
"""

print("app_js.py written.")
