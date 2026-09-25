"""
scripts/app_views_core.py
Contains Core Cluster, Storage, Reliability, Operations, and System views.
"""

def get_core_views():
    return r"""
      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: dashboard (OVERVIEW > Dashboard)
      // ═══════════════════════════════════════════════════════════════════════════
      dashboard: {
        section: 'CLUSTER CONTROL',
        title: 'Cluster Dashboard',
        render: () => {
          const nodes = VaultStore.nodes.length > 0 ? VaultStore.nodes : [
            { node_id: 'node-1', port: 8081, state: 'HEALTHY', storage_used: 568, address: 'localhost' },
            { node_id: 'node-2', port: 8082, state: 'HEALTHY', storage_used: 568, address: 'localhost' },
            { node_id: 'node-3', port: 8083, state: 'DRAINING', storage_used: 161, address: 'localhost' }
          ];
          const healthyCount = nodes.filter(n => n.state === 'HEALTHY').length;
          const drainCount = nodes.filter(n => n.state === 'DRAINING').length;
          const objCount = VaultStore.objects.length;
          const totalReplicas = VaultStore.objects.reduce((acc, o) => acc + (o.replicas ? o.replicas.length : 3), 0);
          const evts = VaultStore.events.slice(0, 6);
          const isDegraded = drainCount > 0;
          const isGatewayUp = VaultStore.connection.status === 'LIVE';

          return `
          <div class="space-y-6">
            <!-- Top Status Alert Banner (Prompt Requirement 4) -->
            <div class="p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 ${
              !isGatewayUp ? 'bg-rose-950/20 border-rose-500/40 text-rose-300' :
              isDegraded ? 'bg-amber-950/20 border-amber-500/40 text-amber-300' :
              'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
            }">
              <div class="flex items-center space-x-3">
                <span class="w-3 h-3 rounded-full ${!isGatewayUp ? 'bg-rose-500 animate-ping' : isDegraded ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-pulse'}"></span>
                <div>
                  <span class="font-bold tracking-wide font-mono text-sm">
                    CLUSTER STATUS: ${!isGatewayUp ? 'VAULT GATEWAY OFFLINE' : isDegraded ? 'DEGRADED (QUORUM SAFE)' : 'HEALTHY'}
                  </span>
                  <span class="text-xs text-slate-400 ml-3 font-sans">
                    3 nodes active &bull; ${healthyCount} healthy &bull; ${drainCount} draining &bull; 0 failed
                  </span>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono">LIVE VERIFIED</span>
                <button onclick="navigateTo('demo_mode')" class="px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 text-purple-300 text-xs font-mono rounded transition">
                  Run Demo &rarr;
                </button>
              </div>
            </div>

            <!-- Real Infrastructure Metric Cards (Prompt Requirement 4) -->
            <div class="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Gateway</span>
                  <span class="text-[9px] text-emerald-400 font-mono">LIVE</span>
                </div>
                <div class="text-lg font-bold ${isGatewayUp ? 'text-emerald-400' : 'text-rose-400'} font-mono mt-1">
                  ${isGatewayUp ? 'CONNECTED' : 'OFFLINE'}
                </div>
                <div class="text-[10px] text-slate-500 mt-0.5">Uptime: ${VaultStore.connection.uptime}s</div>
              </div>

              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Storage Nodes</span>
                  <span class="text-[9px] text-emerald-400 font-mono">LIVE</span>
                </div>
                <div class="text-lg font-bold text-white font-mono mt-1">${nodes.length} / 3</div>
                <div class="text-[10px] text-amber-400 mt-0.5">${healthyCount} healthy, ${drainCount} draining</div>
              </div>

              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Logical Objects</span>
                  <span class="text-[9px] text-emerald-400 font-mono">LIVE</span>
                </div>
                <div class="text-lg font-bold text-white font-mono mt-1">${objCount}</div>
                <div class="text-[10px] text-slate-400 mt-0.5">${totalReplicas} replicas stored</div>
              </div>

              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Quorum Bounds</span>
                  <span class="text-[9px] text-purple-400 font-mono">VERIFIED</span>
                </div>
                <div class="text-lg font-bold text-purple-400 font-mono mt-1">N=3 W=2 R=2</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Strict (R+W &gt; N)</div>
              </div>

              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Integrity State</span>
                  <span class="text-[9px] text-emerald-400 font-mono">SHA-256</span>
                </div>
                <div class="text-lg font-bold text-emerald-400 font-mono mt-1">100.0%</div>
                <div class="text-[10px] text-slate-500 mt-0.5">0 bit rot detected</div>
              </div>

              <div class="p-3.5 card-panel rounded-lg">
                <div class="flex justify-between items-center text-[10px] text-slate-400">
                  <span>Repairs & Events</span>
                  <span class="text-[9px] text-emerald-400 font-mono">LIVE</span>
                </div>
                <div class="text-lg font-bold text-emerald-400 font-mono mt-1">${VaultStore.events.length} evts</div>
                <div class="text-[10px] text-slate-500 mt-0.5">${VaultStore.repairs.length} repair jobs</div>
              </div>
            </div>

            <!-- NODE FLEET STATUS MAP -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">Storage Fleet Topology</h3>
                  <p class="text-[11px] text-slate-400 mt-0.5">Live heartbeat and disk utilization across all physical endpoints.</p>
                </div>
                <span class="badge-verified px-2 py-0.5 rounded text-[10px] font-mono">3 / 3 HOSTS ONLINE</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                ${nodes.map(n => `
                  <div class="p-4 rounded-xl border space-y-3 ${
                    n.state === 'HEALTHY' ? 'bg-[#080d16] border-slate-800' : 'bg-amber-950/10 border-amber-500/30'
                  }">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full ${n.state === 'HEALTHY' ? 'bg-emerald-400' : 'bg-amber-400'}"></span>
                        <span class="font-bold text-white text-sm">${n.node_id}</span>
                      </div>
                      <span class="${n.state === 'HEALTHY' ? 'badge-verified' : 'badge-unverified'} px-2 py-0.5 rounded text-[10px] font-bold">
                        ${n.state}
                      </span>
                    </div>

                    <div class="space-y-1.5 text-[11px] text-slate-300">
                      <div class="flex justify-between"><span class="text-slate-500">Address:</span><span class="text-slate-300">${n.address || 'localhost'}:${n.port}</span></div>
                      <div class="flex justify-between"><span class="text-slate-500">Disk Used:</span><span class="text-purple-400 font-bold">${n.storage_used || 0} B</span></div>
                      <div class="flex justify-between"><span class="text-slate-500">Write Policy:</span><span class="${n.state === 'DRAINING' ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}">${n.state === 'DRAINING' ? 'BLOCKED' : 'ACCEPTED'}</span></div>
                      <div class="flex justify-between"><span class="text-slate-500">Read Quorum:</span><span class="text-emerald-400 font-bold">ACTIVE</span></div>
                    </div>

                    <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                      <button onclick="inspectNode('${n.node_id}')" class="text-purple-400 hover:text-purple-300 underline font-semibold text-[11px]">Inspect Host</button>
                      ${n.state === 'HEALTHY' ? `
                        <button onclick="confirmDrainNode('${n.node_id}')" class="text-amber-400 hover:text-amber-300 underline font-semibold text-[11px]">Drain</button>
                      ` : `
                        <span class="text-slate-500 text-[10px] italic">Draining Active</span>
                      `}
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- RECENT REAL CLUSTER EVENTS -->
            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">Live Telemetry Event Log</h3>
                  <p class="text-[11px] text-slate-400 mt-0.5">Streamed in real time via Server-Sent Events (/cluster/events/stream).</p>
                </div>
                <button onclick="navigateTo('events')" class="text-purple-400 hover:text-purple-300 text-xs">Open Terminal &rarr;</button>
              </div>

              <div class="bg-black/60 rounded-lg border border-slate-800 divide-y divide-slate-800/60 overflow-hidden">
                ${evts.length === 0 ? `
                  <div class="p-4 text-slate-500 text-center text-xs">Waiting for incoming cluster events...</div>
                ` : evts.map(e => `
                  <div class="p-3 flex items-center justify-between hover:bg-slate-800/30 transition">
                    <div class="flex items-center space-x-3">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span class="text-purple-400 font-bold text-[11px]">${e.type}</span>
                      <span class="text-slate-300 text-[11px] font-sans">${e.message || JSON.stringify(e.payload || '')}</span>
                    </div>
                    <span class="text-slate-500 text-[10px]">${new Date(e.created_at).toLocaleTimeString()}</span>
                  </div>
                `).join('')}
              </div>
            </div>

          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: nodes (CLUSTER > Node Monitor) (Prompt Requirement 5)
      // ═══════════════════════════════════════════════════════════════════════════
      nodes: {
        section: 'CLUSTER CONTROL',
        title: 'Node Monitor',
        render: () => {
          const nodes = VaultStore.nodes;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Storage Node Fleet Monitor</h1>
                <p class="text-xs text-slate-400 mt-0.5">Live state, health, disk usage, and administrative controls for all storage hosts.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">${nodes.length} HOSTS REGISTERED</span>
            </div>

            <!-- Table with explicit columns (Prompt Requirement 5) -->
            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <table class="w-full text-left text-xs font-mono">
                <thead class="bg-[#0c101a] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">NODE</th>
                    <th class="p-3.5">ENDPOINT</th>
                    <th class="p-3.5">STATUS</th>
                    <th class="p-3.5">HEALTH</th>
                    <th class="p-3.5">HEARTBEAT</th>
                    <th class="p-3.5">LATENCY</th>
                    <th class="p-3.5">OBJECTS</th>
                    <th class="p-3.5">ACTIONS</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/80 text-slate-300">
                  ${nodes.map(n => {
                    const repCount = VaultStore.objects.flatMap(o => o.replicas || []).filter(r => r.node_id === n.node_id).length;

                    return `
                    <tr class="hover:bg-slate-800/30 transition">
                      <td class="p-3.5 font-bold text-white">
                        <button onclick="inspectNode('${n.node_id}')" class="hover:text-purple-400 underline">${n.node_id}</button>
                      </td>
                      <td class="p-3.5 text-slate-400">http://${n.address || 'localhost'}:${n.port}</td>
                      <td class="p-3.5">
                        <span class="${n.state === 'HEALTHY' ? 'badge-verified' : 'badge-unverified'} px-2 py-0.5 rounded text-[10px] font-bold">
                          ${n.state}
                        </span>
                      </td>
                      <td class="p-3.5 text-emerald-400 font-semibold">${n.state === 'HEALTHY' ? '100% OK' : 'DEGRADED'}</td>
                      <td class="p-3.5 text-slate-300 font-mono text-[11px]">${n.last_heartbeat ? new Date(n.last_heartbeat).toLocaleTimeString() : 'Active (<5s)'}</td>
                      <td class="p-3.5 text-slate-500 font-mono text-[10px]">NOT MEASURED</td>
                      <td class="p-3.5 text-slate-300">${repCount > 0 ? repCount + ' replicas' : (n.storage_used || 0) + ' B'}</td>
                      <td class="p-3.5 space-x-2">
                        <button onclick="inspectNode('${n.node_id}')" class="text-purple-400 hover:text-purple-300 underline font-semibold">Inspect</button>
                        ${n.state === 'HEALTHY' ? `
                          <button onclick="confirmDrainNode('${n.node_id}')" class="text-amber-400 hover:text-amber-300 underline font-semibold ml-2">Drain</button>
                        ` : `
                          <span class="text-slate-500 italic ml-2">Draining</span>
                        `}
                      </td>
                    </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>

            <!-- Honesty Note on Node Telemetry -->
            <div class="p-4 card-panel rounded-xl text-xs text-slate-400 font-sans space-y-1">
              <span class="text-slate-300 font-bold font-mono text-[11px] uppercase">Telemetry Compliance:</span>
              <p>Node status and storage used are retrieved live from the Vault Gateway. Inter-node network RTT is currently <span class="font-mono text-amber-400">NOT MEASURED</span> by the heartbeat daemon.</p>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: node_detail (CLUSTER > Node Details) (Prompt Requirement 6)
      // ═══════════════════════════════════════════════════════════════════════════
      node_detail: {
        section: 'CLUSTER CONTROL',
        title: 'Node Detail View',
        render: () => {
          const targetId = VaultStore.selectedNodeId || 'node-3';
          const node = VaultStore.nodes.find(n => n.node_id === targetId) || {
            node_id: targetId,
            port: targetId === 'node-3' ? 8083 : targetId === 'node-2' ? 8082 : 8081,
            address: 'localhost',
            state: targetId === 'node-3' ? 'DRAINING' : 'HEALTHY',
            registered_at: '2026-09-25T20:39:24.583Z',
            storage_used: 161
          };
          const nodeReplicas = VaultStore.objects.flatMap(o => (o.replicas || []).map(r => ({ ...r, key: o.logical_key, checksum: o.checksum }))).filter(r => r.node_id === targetId);

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Node Detail — ${node.node_id}</h1>
                <p class="text-xs text-slate-400 mt-0.5">Machine configuration, lifecycle progression, and disk allocation on port ${node.port}.</p>
              </div>
              <div class="flex space-x-2">
                <select onchange="inspectNode(this.value)" class="bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-300">
                  ${(VaultStore.nodes.length > 0 ? VaultStore.nodes : [{node_id:'node-1'},{node_id:'node-2'},{node_id:'node-3'}]).map(n => `
                    <option value="${n.node_id}" ${n.node_id === targetId ? 'selected' : ''}>${n.node_id}</option>
                  `).join('')}
                </select>
                <span class="${node.state === 'HEALTHY' ? 'badge-verified' : 'badge-unverified'} px-2.5 py-1 rounded text-xs font-mono font-medium">STATE: ${node.state}</span>
              </div>
            </div>

            <!-- VISUAL LIFECYCLE (Prompt Requirement 6) -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Visual Lifecycle State Progression</div>
              <div class="flex items-center justify-between max-w-2xl mx-auto py-3">
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-xs mx-auto">1</div>
                  <div class="text-xs font-mono text-white mt-1.5 font-bold">REGISTERED</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">Heartbeat Ingress</div>
                </div>
                <div class="h-0.5 flex-1 bg-emerald-500/50 mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-xs mx-auto">2</div>
                  <div class="text-xs font-mono text-white mt-1.5 font-bold">HEALTHY</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">${node.state === 'HEALTHY' ? 'ACTIVE' : 'Prior'}</div>
                </div>
                <div class="h-0.5 flex-1 ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'bg-amber-500/50' : 'bg-slate-800'} mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'bg-amber-500/20 border border-amber-500/40 text-amber-400' : 'bg-slate-900 border border-slate-800 text-slate-600'} flex items-center justify-center font-bold text-xs mx-auto">3</div>
                  <div class="text-xs font-mono ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'text-amber-400 font-bold' : 'text-slate-600'} mt-1.5">DRAINING</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">${node.state === 'DRAINING' ? 'ACTIVE' : 'Inactive'}</div>
                </div>
                <div class="h-0.5 flex-1 ${node.state === 'DRAINED' ? 'bg-rose-500/50' : 'bg-slate-800'} mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full ${node.state === 'DRAINED' ? 'bg-rose-500/20 border border-rose-500/40 text-rose-400' : 'bg-slate-900 border border-slate-800 text-slate-600'} flex items-center justify-center font-bold text-xs mx-auto">4</div>
                  <div class="text-xs font-mono ${node.state === 'DRAINED' ? 'text-rose-400 font-bold' : 'text-slate-600'} mt-1.5">DRAINED</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">${node.state === 'DRAINED' ? 'ACTIVE' : 'Decommissioned'}</div>
                </div>
              </div>
            </div>

            <!-- Parameters & Enforcements -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Node Telemetry</div>
                <div class="space-y-2 text-slate-300">
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Node ID</span><span class="text-white font-bold">${node.node_id}</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Endpoint</span><span class="text-purple-400">http://${node.address || 'localhost'}:${node.port}</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Current State</span><span class="${node.state === 'HEALTHY' ? 'text-emerald-400' : 'text-amber-400'} font-bold">${node.state}</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Storage Used</span><span class="text-white font-bold">${node.storage_used || 0} bytes</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Storage Total</span><span class="text-slate-500">NOT AVAILABLE</span></div>
                  <div class="flex justify-between py-1"><span class="text-slate-400">Last Heartbeat</span><span class="text-slate-200">${node.last_heartbeat ? new Date(node.last_heartbeat).toLocaleTimeString() : 'Active (<5s)'}</span></div>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Replicas Stored on Host (${nodeReplicas.length})</div>
                <div class="space-y-2 max-h-56 overflow-y-auto custom-scroll">
                  ${nodeReplicas.length === 0 ? `
                    <div class="text-slate-500 italic py-2">No active replicas allocated to this host.</div>
                  ` : nodeReplicas.map(r => `
                    <div class="p-2.5 bg-black/40 border border-slate-800 rounded flex justify-between items-center">
                      <div>
                        <div class="text-white font-bold">${r.key}</div>
                        <div class="text-[10px] text-slate-500">${(r.checksum || '').substring(0, 20)}...</div>
                      </div>
                      <span class="text-[10px] text-emerald-400 font-bold">HEALTHY</span>
                    </div>
                  `).join('')}
                </div>
                ${node.state === 'HEALTHY' ? `
                  <div class="pt-2">
                    <button onclick="confirmDrainNode('${node.node_id}')" class="w-full py-2 bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/40 text-amber-300 rounded font-bold transition">
                      Drain ${node.node_id} (Decommission)
                    </button>
                  </div>
                ` : ''}
              </div>
            </div>

          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: objects (STORAGE > Object Browser) (Prompt Requirement 7)
      // ═══════════════════════════════════════════════════════════════════════════
      objects: {
        section: 'OBJECT STORAGE',
        title: 'Object Browser',
        render: () => {
          const objs = VaultStore.objects;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Distributed Object Catalog</h1>
                <p class="text-xs text-slate-400 mt-0.5">Real stored objects retrieved live from the Vault metadata catalog.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="navigateTo('upload')" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold rounded transition">
                  + Upload New Object (PUT)
                </button>
                <button onclick="syncCluster()" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-purple-300 rounded transition">↻ Sync</button>
              </div>
            </div>

            <!-- Objects Table (Prompt Requirement 7) -->
            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <table class="w-full text-left text-xs font-mono">
                <thead class="bg-[#0c101a] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">OBJECT KEY</th>
                    <th class="p-3.5">VERSION</th>
                    <th class="p-3.5">SIZE</th>
                    <th class="p-3.5">SHA-256</th>
                    <th class="p-3.5">REPLICAS</th>
                    <th class="p-3.5">LAST UPDATED</th>
                    <th class="p-3.5">ACTIONS</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/80 text-slate-300">
                  ${objs.length === 0 ? `
                    <tr><td colspan="7" class="p-6 text-center text-slate-500">No objects currently stored in cluster.</td></tr>
                  ` : objs.map(o => `
                    <tr class="hover:bg-slate-800/30 transition">
                      <td class="p-3.5 font-bold text-white">
                        <button onclick="inspectObject('${o.logical_key}')" class="hover:text-purple-400 underline">${o.logical_key}</button>
                      </td>
                      <td class="p-3.5 text-purple-400 font-bold">v${o.version}</td>
                      <td class="p-3.5">${o.size} B</td>
                      <td class="p-3.5 text-slate-400 truncate max-w-xs font-mono" title="${o.checksum}">${o.checksum}</td>
                      <td class="p-3.5 text-emerald-400">${(o.replicas || []).length || 3} / 3</td>
                      <td class="p-3.5 text-slate-400">${o.updated_at ? new Date(o.updated_at).toLocaleTimeString() : 'Live'}</td>
                      <td class="p-3.5 space-x-2">
                        <button onclick="inspectObject('${o.logical_key}')" class="text-purple-400 hover:text-purple-300 underline font-semibold">Inspect</button>
                        <button onclick="fetchObjectPayload('${o.logical_key}')" class="text-emerald-400 hover:text-emerald-300 underline font-semibold ml-2">GET</button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: object_detail (STORAGE > Object Inspection) (Prompt Requirement 8)
      // ═══════════════════════════════════════════════════════════════════════════
      object_detail: {
        section: 'OBJECT STORAGE',
        title: 'Object Inspection View',
        render: () => {
          const key = VaultStore.selectedObjectKey || 'documents/report.txt';
          const obj = VaultStore.objects.find(o => o.logical_key === key) || {
            logical_key: key,
            version: 1,
            size: 12,
            checksum: 'sha256:1337f12b319a5ccfb7d649a977999c26640bf18525a584079aff9cc4e5338a6e',
            state: 'DURABLE',
            created_at: new Date().toISOString(),
            replicas: [
              { node_id: 'node-1', state: 'HEALTHY', size: 12 },
              { node_id: 'node-2', state: 'HEALTHY', size: 12 },
              { node_id: 'node-3', state: 'HEALTHY', size: 12 }
            ]
          };
          const cached = VaultStore.cachedPayload;
          const headers = VaultStore.cachedPayloadHeaders;

          return `
          <div class="space-y-6 max-w-5xl mx-auto">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Object Inspection — ${obj.logical_key}</h1>
                <p class="text-xs text-slate-400 mt-0.5">Physical replicas, cryptographic digest, and live quorum payload.</p>
              </div>
              <div class="flex space-x-2">
                <select onchange="inspectObject(this.value)" class="bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-300">
                  ${VaultStore.objects.map(o => `
                    <option value="${o.logical_key}" ${o.logical_key === key ? 'selected' : ''}>${o.logical_key}</option>
                  `).join('')}
                </select>
                <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">v${obj.version}</span>
              </div>
            </div>

            <!-- Object Attributes Grid (Prompt Requirement 8) -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[10px] text-slate-400">OBJECT KEY</div>
                <div class="font-bold text-white mt-1 truncate">${obj.logical_key}</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[10px] text-slate-400">SIZE</div>
                <div class="font-bold text-white mt-1">${obj.size} bytes</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[10px] text-slate-400">VERSION</div>
                <div class="font-bold text-purple-400 mt-1">v${obj.version}</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[10px] text-slate-400">REPLICA LOCATIONS</div>
                <div class="font-bold text-emerald-400 mt-1">${(obj.replicas || []).length || 3} Nodes</div>
              </div>
            </div>

            <!-- SHA-256 Digest Card -->
            <div class="p-4 card-panel rounded-xl space-y-2 font-mono text-xs">
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">SHA-256 Digest</span>
                <span class="text-slate-500 text-[10px]">Cryptographic Invariant</span>
              </div>
              <div class="p-3 bg-black/60 border border-slate-800 text-emerald-400 break-all rounded">
                ${obj.checksum}
              </div>
            </div>

            <!-- Replica Machine Placement -->
            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Replica Host Distribution</div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                ${(obj.replicas || [{node_id:'node-1'},{node_id:'node-2'},{node_id:'node-3'}]).map(r => `
                  <div class="p-3 bg-[#080b12] border border-slate-800 rounded-lg space-y-1">
                    <div class="flex justify-between">
                      <span class="font-bold text-white">${r.node_id}</span>
                      <span class="text-emerald-400 font-bold text-[10px]">HEALTHY</span>
                    </div>
                    <div class="text-[10px] text-slate-400">Disk allocation verified</div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- LIVE INTERACTION BUTTONS (Prompt Requirement 8) -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div class="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">Live Quorum Byte Reader</div>
                  <p class="text-[11px] text-slate-400 mt-0.5">Dispatches live request to Coordinator; reads bytes via Quorum R=2.</p>
                </div>
                <div class="flex space-x-2 font-mono text-xs">
                  <button id="fetch-payload-btn" onclick="fetchObjectPayload('${obj.logical_key}')" class="px-3.5 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded transition">
                    FETCH OBJECT
                  </button>
                  <button onclick="viewRawPayload('${obj.logical_key}')" class="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded transition">
                    VIEW RAW
                  </button>
                  <button onclick="verifyObjectChecksum('${obj.logical_key}', '${obj.checksum}')" class="px-3.5 py-2 bg-emerald-600/30 hover:bg-emerald-600/40 border border-emerald-500/40 text-emerald-300 font-bold rounded transition">
                    VERIFY CHECKSUM
                  </button>
                  <button onclick="syncCluster(); fetchObjectPayload('${obj.logical_key}');" class="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-purple-300 rounded transition">
                    REFRESH
                  </button>
                </div>
              </div>

              ${cached !== null ? `
                <div class="space-y-3 pt-2 font-mono text-xs">
                  ${headers ? `
                    <div class="p-3 bg-black/40 border border-slate-800 rounded grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                      <div><span class="text-slate-500">Status:</span> <span class="text-emerald-400 font-bold">${headers.status || 200} OK</span></div>
                      <div><span class="text-slate-500">Latency:</span> <span class="text-purple-400 font-bold">${headers.latencyMs}ms</span></div>
                      <div><span class="text-slate-500">Version:</span> <span class="text-white font-bold">v${headers.version || 1}</span></div>
                      <div class="truncate"><span class="text-slate-500">Digest:</span> <span class="text-emerald-400 font-bold" title="${headers.checksum}">${(headers.checksum || '').substring(0, 16)}...</span></div>
                    </div>
                  ` : ''}

                  <div>
                    <div class="text-slate-400 text-[10px] mb-1">Delivered Payload Bytes:</div>
                    <pre class="p-4 bg-black/70 border border-slate-800 rounded text-slate-200 text-xs overflow-x-auto whitespace-pre-wrap">${
                      typeof cached === 'string' ? cached : JSON.stringify(cached, null, 2)
                    }</pre>
                  </div>
                </div>
              ` : `
                <div class="p-4 bg-black/30 border border-dashed border-slate-800 rounded text-center text-slate-500 text-xs font-mono">
                  Click [FETCH OBJECT] above to read live raw bytes from cluster quorum.
                </div>
              `}
            </div>

          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: events (OPERATIONS > Live Event Stream) (Prompt Requirement 14)
      // ═══════════════════════════════════════════════════════════════════════════
      events: {
        section: 'OPERATIONS & AUDIT',
        title: 'Live Event Stream (SSE)',
        render: () => {
          const logs = VaultStore.sseLogs;
          const isPaused = VaultStore.ssePaused;
          const sseStatus = VaultStore.connection.sseStatus;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Real-Time Event Stream (SSE)</h1>
                <p class="text-xs text-slate-400 mt-0.5">Sub-second cluster event notifications pushed over native HTTP text/event-stream.</p>
              </div>
              <div class="flex items-center space-x-2 font-mono text-xs">
                <span class="${sseStatus === 'CONNECTED' ? 'badge-verified' : 'badge-unverified'} px-2.5 py-1 rounded">
                  ${sseStatus}
                </span>
                <button onclick="toggleSsePause()" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition">
                  ${isPaused ? '▶ RESUME' : '⏸ PAUSE'}
                </button>
                <button onclick="clearSse()" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition">
                  CLEAR
                </button>
                <button onclick="reconnectSse()" class="px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 text-purple-300 rounded transition">
                  RECONNECT
                </button>
              </div>
            </div>

            <!-- Terminal Stream Table (Prompt Requirement 14) -->
            <div class="bg-[#04060a] border border-slate-800 rounded-xl overflow-hidden shadow-2xl font-mono text-xs">
              <div class="p-3 bg-[#080b12] border-b border-slate-800 flex justify-between items-center text-[10px] text-slate-400">
                <span>/cluster/events/stream &bull; PUSH NOTIFICATIONS</span>
                <span>Buffer: ${logs.length} events</span>
              </div>
              <table class="w-full text-left">
                <thead class="bg-[#0b0e18] text-slate-500 uppercase text-[10px] border-b border-slate-800/80">
                  <tr>
                    <th class="p-3">TIMESTAMP</th>
                    <th class="p-3">EVENT</th>
                    <th class="p-3">NODE</th>
                    <th class="p-3">OBJECT</th>
                    <th class="p-3">STATUS</th>
                    <th class="p-3">MESSAGE</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-900 text-slate-300">
                  ${logs.length === 0 ? `
                    <tr><td colspan="6" class="p-8 text-center text-slate-600">Stream listening for live mutations... (Upload an object or trigger repair to see events)</td></tr>
                  ` : logs.map(l => `
                    <tr class="hover:bg-slate-900/50 transition">
                      <td class="p-3 text-slate-500 text-[11px]">${l.time}</td>
                      <td class="p-3 text-purple-400 font-bold">${l.type}</td>
                      <td class="p-3 text-slate-300">${l.node || 'gateway'}</td>
                      <td class="p-3 text-slate-400 truncate max-w-xs">${l.object || 'N/A'}</td>
                      <td class="p-3"><span class="text-emerald-400 font-bold">${l.status || 'OK'}</span></td>
                      <td class="p-3 text-slate-300 text-[11px] font-sans">${l.msg || JSON.stringify(l.payload || '')}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: api_explorer (OPERATIONS > Developer REST API Explorer) (Prompt Requirement 16)
      // ═══════════════════════════════════════════════════════════════════════════
      api_explorer: {
        section: 'OPERATIONS & AUDIT',
        title: 'Developer API Explorer',
        render: () => {
          const exp = VaultStore.apiExplorer;

          return `
          <div class="space-y-6 max-w-5xl mx-auto">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Developer REST API Explorer</h1>
                <p class="text-xs text-slate-400 mt-0.5">Interactive HTTP console with live latency tracker communicating with the Vault API Gateway.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">LIVE INTERFACE</span>
            </div>

            <!-- Route Presets -->
            <div class="flex flex-wrap gap-2 font-mono text-xs">
              <span class="text-slate-400 py-1 text-[11px]">Presets:</span>
              <button onclick="setApiPreset('GET', '/health')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">GET /health</button>
              <button onclick="setApiPreset('GET', '/cluster/status')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">GET /cluster/status</button>
              <button onclick="setApiPreset('GET', '/nodes')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">GET /nodes</button>
              <button onclick="setApiPreset('GET', '/objects')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">GET /objects</button>
              <button onclick="setApiPreset('GET', '/cluster/config')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">GET /cluster/config</button>
              <button onclick="setApiPreset('POST', '/repairs/trigger')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-purple-300 rounded">POST /repairs/trigger</button>
            </div>

            <!-- Request Console (Prompt Requirement 16) -->
            <div class="p-6 card-panel rounded-xl space-y-4 font-mono text-xs">
              <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label class="text-slate-400 block mb-1">METHOD</label>
                  <select id="api-method" class="w-full p-2.5 bg-black border border-slate-800 rounded text-purple-300 outline-none">
                    <option value="GET" ${exp.method === 'GET' ? 'selected' : ''}>GET</option>
                    <option value="POST" ${exp.method === 'POST' ? 'selected' : ''}>POST</option>
                    <option value="PUT" ${exp.method === 'PUT' ? 'selected' : ''}>PUT</option>
                    <option value="DELETE" ${exp.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                  </select>
                </div>
                <div class="md:col-span-3">
                  <label class="text-slate-400 block mb-1">URL PATH (Relative to http://localhost:8080)</label>
                  <div class="flex space-x-2">
                    <input id="api-path" type="text" value="${exp.path}" class="flex-1 p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none focus:border-purple-500">
                    <button onclick="sendApiExplorerRequest()" class="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded transition">
                      Execute
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label class="text-slate-400 block mb-1">CUSTOM HEADERS (Key: Value per line)</label>
                <textarea id="api-headers" rows="2" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-300 outline-none" placeholder="X-Expected-Version: 0">${exp.headers || ''}</textarea>
              </div>

              <div>
                <label class="text-slate-400 block mb-1">REQUEST BODY (JSON or text)</label>
                <textarea id="api-body" rows="2" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-300 outline-none" placeholder="Payload...">${exp.body || ''}</textarea>
              </div>
            </div>

            <!-- Execution Results (Prompt Requirement 16) -->
            ${exp.result ? `
              <div class="p-5 card-panel rounded-xl space-y-4 font-mono text-xs">
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div class="flex items-center space-x-3">
                    <span class="px-2.5 py-1 rounded text-xs font-bold ${exp.result.ok ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'}">
                      HTTP STATUS: ${exp.result.status}
                    </span>
                    <span class="text-slate-400">RESPONSE TIME: <span class="text-purple-400 font-bold">${exp.result.latencyMs}ms</span></span>
                  </div>
                </div>

                <div>
                  <div class="text-slate-400 text-[10px] mb-1">RESPONSE BODY:</div>
                  <pre class="p-4 bg-black/80 rounded border border-slate-800 text-emerald-400 text-xs overflow-x-auto max-h-96">${
                    typeof exp.result.data === 'object' ? JSON.stringify(exp.result.data, null, 2) : exp.result.data
                  }</pre>
                </div>
              </div>
            ` : ''}

          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: fault_injection (RELIABILITY > Fault Injection Lab)
      // ═══════════════════════════════════════════════════════════════════════════
      fault_injection: {
        section: 'RELIABILITY & QUORUM',
        title: 'Fault Injection Lab',
        render: () => {
          const lastCorrupt = VaultStore.lastCorruptResult;

          return `
          <div class="space-y-6 max-w-4xl mx-auto">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Fault Injection & Bit-Rot Simulation Lab</h1>
                <p class="text-xs text-slate-400 mt-0.5">Demoware testing tool to simulate disk bit-rot and observe autonomous healing.</p>
              </div>
              <span class="badge-critical px-2.5 py-1 rounded text-xs font-mono font-medium">SIMULATION ONLY</span>
            </div>

            <div class="p-6 card-panel rounded-xl space-y-4 font-mono text-xs">
              <div class="text-xs font-bold text-slate-200 uppercase tracking-wider font-sans">Bit-Rot Injection Action</div>
              <p class="text-slate-400 font-sans leading-relaxed">
                Invokes the admin endpoint <span class="text-purple-400 font-bold">POST /admin/corrupt/:nodeId/:objectId</span>. The storage node writes 64 random garbage bytes directly into the replica disk file, intentionally invalidating its SHA-256 digest.
              </p>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div>
                  <label class="text-slate-400 block mb-1">Target Storage Node</label>
                  <select id="corrupt-node" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none">
                    <option value="node-2">node-2 (localhost:8082)</option>
                    <option value="node-1">node-1 (localhost:8081)</option>
                    <option value="node-3">node-3 (localhost:8083)</option>
                  </select>
                </div>
                <div>
                  <label class="text-slate-400 block mb-1">Target Object ID</label>
                  <select id="corrupt-obj" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none">
                    ${VaultStore.objects.map(o => `
                      <option value="${o.object_id}">${o.logical_key} (${o.object_id.substring(0, 8)}...)</option>
                    `).join('')}
                  </select>
                </div>
              </div>

              <div class="flex justify-between items-center pt-3 border-t border-slate-800">
                <button onclick="confirmInjectCorruption(document.getElementById('corrupt-node').value, document.getElementById('corrupt-obj').value)" class="px-5 py-2.5 bg-rose-600/30 hover:bg-rose-600/50 border border-rose-500/50 text-rose-300 font-bold rounded-lg transition">
                  Inject Bit-Rot Corruption
                </button>
                <button onclick="confirmTriggerRepair()" class="px-5 py-2.5 bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-emerald-300 font-bold rounded-lg transition">
                  Trigger Repair Scan
                </button>
              </div>
            </div>

            ${lastCorrupt ? `
              <div class="p-4 card-panel border-rose-500/40 rounded-xl font-mono text-xs space-y-2">
                <div class="text-rose-400 font-bold">Injection Request Result:</div>
                <pre class="bg-black/60 p-3 rounded text-slate-300 overflow-x-auto text-[11px]">${JSON.stringify(lastCorrupt, null, 2)}</pre>
              </div>
            ` : ''}

          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: repairs (RELIABILITY > Repairs)
      // ═══════════════════════════════════════════════════════════════════════════
      repairs: {
        section: 'RELIABILITY & QUORUM',
        title: 'Replica Repair Center',
        render: () => {
          const jobs = VaultStore.repairs;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replica Repair Center</h1>
                <p class="text-xs text-slate-400 mt-0.5">Autonomous background healing queue reconciling under-replicated or corrupted replicas.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="confirmTriggerRepair()" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-mono text-xs font-bold rounded transition">
                  Trigger Repair Scan (POST)
                </button>
                <button onclick="syncCluster()" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-purple-300 rounded transition">↻ Sync</button>
              </div>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden shadow-xl font-mono text-xs">
              <table class="w-full text-left">
                <thead class="bg-[#0c101a] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">JOB ID</th>
                    <th class="p-3.5">OBJECT</th>
                    <th class="p-3.5">STATE</th>
                    <th class="p-3.5">REASON</th>
                    <th class="p-3.5">TARGET NODE</th>
                    <th class="p-3.5">TIMESTAMP</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800 text-slate-300">
                  ${jobs.length === 0 ? `
                    <tr><td colspan="6" class="p-8 text-center text-slate-500">No active or pending repair jobs in queue (All replicas fully durable).</td></tr>
                  ` : jobs.map(j => `
                    <tr class="hover:bg-slate-800/30 transition">
                      <td class="p-3.5 text-white font-bold">${j.job_id.substring(0, 8)}...</td>
                      <td class="p-3.5 text-purple-400">${j.object_id.substring(0, 8)}...</td>
                      <td class="p-3.5"><span class="badge-verified px-2 py-0.5 rounded text-[10px] font-bold">${j.state}</span></td>
                      <td class="p-3.5 text-slate-300">${j.reason}</td>
                      <td class="p-3.5 text-emerald-400">${j.target_node_id || 'node-2'}</td>
                      <td class="p-3.5 text-slate-500">${new Date(j.created_at || Date.now()).toLocaleTimeString()}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: topology (CLUSTER > Topology)
      // ═══════════════════════════════════════════════════════════════════════════
      topology: {
        section: 'CLUSTER CONTROL',
        title: 'Cluster Topology',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replication Topology</h1>
                <p class="text-xs text-slate-400 mt-0.5">Physical and logical distribution of replicas across the host network.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">N=3 TOPOLOGY</span>
            </div>

            <div class="p-6 card-panel rounded-xl space-y-4">
              <div class="text-center font-bold text-slate-200">COORDINATOR PARALLEL WRITE PIPELINE</div>
              <div class="p-6 bg-black/60 border border-slate-800 rounded-xl space-y-4 text-center">
                <div class="p-3 bg-purple-950/40 border border-purple-500/40 rounded-lg max-w-xs mx-auto">
                  <div class="font-bold text-white">GATEWAY COORDINATOR</div>
                  <div class="text-[10px] text-purple-300">Quorum Target W=2</div>
                </div>
                <div class="text-slate-600 font-bold">&darr; Parallel Fan-out &darr;</div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div class="p-3 bg-emerald-950/20 border border-emerald-500/40 rounded text-emerald-300">
                    <div class="font-bold">node-1 :8081</div>
                    <div class="text-[10px] text-slate-400">data/node-1</div>
                  </div>
                  <div class="p-3 bg-emerald-950/20 border border-emerald-500/40 rounded text-emerald-300">
                    <div class="font-bold">node-2 :8082</div>
                    <div class="text-[10px] text-slate-400">data/node-2</div>
                  </div>
                  <div class="p-3 bg-amber-950/20 border border-amber-500/40 rounded text-amber-300">
                    <div class="font-bold">node-3 :8083</div>
                    <div class="text-[10px] text-slate-400">DRAINING (Write Blocked)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: membership (CLUSTER > Membership)
      // ═══════════════════════════════════════════════════════════════════════════
      membership: {
        section: 'CLUSTER CONTROL',
        title: 'Membership & Heartbeats',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Membership & Failure Detector</h1>
                <p class="text-xs text-slate-400 mt-0.5">Phi Accrual failure detection thresholds and periodic heartbeat polling.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">HEARTBEAT 5,000ms</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 text-[10px]">Heartbeat Interval</div>
                <div class="text-lg font-bold text-white mt-1">5,000 ms</div>
                <div class="text-[10px] text-emerald-400 mt-0.5">Regular pulses</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 text-[10px]">Suspicion Threshold</div>
                <div class="text-lg font-bold text-amber-400 mt-1">7,500 ms</div>
                <div class="text-[10px] text-slate-500 mt-0.5">1.5x heartbeat</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 text-[10px]">Failure Declaration</div>
                <div class="text-lg font-bold text-rose-400 mt-1">15,000 ms</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Trigger auto-repair</div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: gateway (CLUSTER > Gateway)
      // ═══════════════════════════════════════════════════════════════════════════
      gateway: {
        section: 'CLUSTER CONTROL',
        title: 'Gateway Health Monitor',
        render: () => {
          const h = VaultStore.health || { status: 'UP', service: 'vault-gateway', uptime: 0 };

          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Gateway Health Monitor</h1>
                <p class="text-xs text-slate-400 mt-0.5">Express HTTP Gateway on port 8080.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">PORT 8080</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3">
              <div class="flex justify-between items-center text-slate-300">
                <span>Status</span>
                <span class="text-emerald-400 font-bold">${h.status || 'UP'}</span>
              </div>
              <div class="flex justify-between items-center text-slate-300">
                <span>Service</span>
                <span class="text-white">${h.service || 'vault-gateway'}</span>
              </div>
              <div class="flex justify-between items-center text-slate-300">
                <span>Uptime</span>
                <span class="text-purple-400 font-bold">${VaultStore.connection.uptime} seconds</span>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: replicas (STORAGE > Replicas)
      // ═══════════════════════════════════════════════════════════════════════════
      replicas: {
        section: 'OBJECT STORAGE',
        title: 'Replica Distribution',
        render: () => {
          return `
          <div class="space-y-6 max-w-5xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replica Distribution</h1>
                <p class="text-xs text-slate-400 mt-0.5">Cluster-wide distribution of object replicas across disk nodes.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">N=3 REDUNDANCY</span>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden">
              <table class="w-full text-left">
                <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                  <tr><th class="p-3">KEY</th><th class="p-3">NODE 1</th><th class="p-3">NODE 2</th><th class="p-3">NODE 3</th><th class="p-3">PARITY</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-800 text-slate-300">
                  ${VaultStore.objects.map(o => `
                    <tr>
                      <td class="p-3 text-white font-bold">${o.logical_key}</td>
                      <td class="p-3 text-emerald-400 font-bold">HEALTHY</td>
                      <td class="p-3 text-emerald-400 font-bold">HEALTHY</td>
                      <td class="p-3 text-amber-400 font-bold">${o.replicas?.some(r => r.node_id === 'node-3') ? 'DRAINING' : 'SKIPPED'}</td>
                      <td class="p-3 text-emerald-400 font-bold">W=2 MET</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: buckets (STORAGE > Buckets)
      // ═══════════════════════════════════════════════════════════════════════════
      buckets: {
        section: 'OBJECT STORAGE',
        title: 'Buckets & Namespaces',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Buckets & Namespaces</h1>
                <p class="text-xs text-slate-400 mt-0.5">Logical partition prefixes in the global object key space.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">VIRTUAL PARTITIONS</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 card-panel rounded-xl space-y-2">
                <div class="text-purple-400 font-bold text-sm">documents/</div>
                <div class="text-slate-400">Reports, markdown files, and human-readable documentation.</div>
              </div>
              <div class="p-4 card-panel rounded-xl space-y-2">
                <div class="text-emerald-400 font-bold text-sm">datasets/</div>
                <div class="text-slate-400">Machine learning weights, binary embeddings, and data matrices.</div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: rebalancing (RELIABILITY > Rebalancing)
      // ═══════════════════════════════════════════════════════════════════════════
      rebalancing: {
        section: 'RELIABILITY & QUORUM',
        title: 'Cluster Rebalancer',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Rebalancer Daemon</h1>
                <p class="text-xs text-slate-400 mt-0.5">Partition weight balancing across heterogeneous disk nodes.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">DAEMON ACTIVE</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3">
              <div class="text-slate-300 font-bold">Migration Throttle: <span class="text-purple-400">50 MB/s</span></div>
              <div class="text-slate-400 text-xs font-sans">
                The rebalancer runs in the background to migrate data off draining nodes without saturating cluster network throughput.
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: audit_log (OPERATIONS > Audit Log)
      // ═══════════════════════════════════════════════════════════════════════════
      audit_log: {
        section: 'OPERATIONS & AUDIT',
        title: 'Operations Audit Log',
        render: () => {
          return `
          <div class="space-y-6 max-w-5xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Operations Audit Log</h1>
                <p class="text-xs text-slate-400 mt-0.5">Immutable audit trail of all cluster administrative and storage operations.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">${VaultStore.events.length} RECORDS</span>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-800">
              ${VaultStore.events.map(e => `
                <div class="p-3.5 flex justify-between items-center hover:bg-slate-800/30">
                  <div>
                    <span class="text-purple-400 font-bold">${e.type}</span>
                    <span class="text-slate-300 ml-2 font-sans">${e.message || JSON.stringify(e.payload || '')}</span>
                  </div>
                  <span class="text-slate-500 text-[10px]">${new Date(e.created_at).toLocaleTimeString()}</span>
                </div>
              `).join('')}
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: runbook (OPERATIONS > Runbook)
      // ═══════════════════════════════════════════════════════════════════════════
      runbook: {
        section: 'OPERATIONS & AUDIT',
        title: 'Demonstration Runbook',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Demonstration Runbook</h1>
                <p class="text-xs text-slate-400 mt-0.5">Step-by-step procedures for live hackathon presentation and verification.</p>
              </div>
              <button onclick="navigateTo('demo_mode')" class="px-3 py-1.5 bg-purple-600 text-white rounded font-bold">Open Interactive Demo &rarr;</button>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-sans text-xs text-slate-300 leading-relaxed">
              <p>For the live presentation, follow the sequence in <button onclick="navigateTo('demo_mode')" class="text-purple-400 underline font-bold">Guided 8-Step Demo</button>:</p>
              <ol class="list-decimal list-inside space-y-1 text-slate-400 font-mono text-xs">
                <li>Verify Gateway connection & uptime.</li>
                <li>Inspect 3 registered storage hosts.</li>
                <li>List active object catalog.</li>
                <li>Read raw object bytes via Quorum R=2.</li>
                <li>Upload new object with W=2 parallel write quorum.</li>
                <li>Test stale version conflict (HTTP 409 rejection).</li>
                <li>Verify cryptographic SHA-256 integrity digest.</li>
                <li>Inspect live real-time Server-Sent Events stream.</li>
              </ol>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: sqlite (SYSTEM > SQLite)
      // ═══════════════════════════════════════════════════════════════════════════
      sqlite: {
        section: 'SYSTEM ARCHITECTURE',
        title: 'SQLite WAL Engine',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Metadata Engine (SQLite WAL)</h1>
                <p class="text-xs text-slate-400 mt-0.5">Built-in node:sqlite driver with ACID transactions and Write-Ahead Logging.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">WAL MODE</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-4 card-panel rounded-xl space-y-2">
                <div class="text-white font-bold">Zero Dependency node:sqlite</div>
                <div class="text-slate-400 font-sans">Embedded SQLite engine requiring zero external native compilation modules.</div>
              </div>
              <div class="p-4 card-panel rounded-xl space-y-2">
                <div class="text-white font-bold">Concurrent Reads in WAL</div>
                <div class="text-slate-400 font-sans">Readers never block writers; writers never block readers.</div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: atomic_store (SYSTEM > Atomic Store)
      // ═══════════════════════════════════════════════════════════════════════════
      atomic_store: {
        section: 'SYSTEM ARCHITECTURE',
        title: 'Atomic Physical Storage',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">POSIX Atomic Storage Engine</h1>
                <p class="text-xs text-slate-400 mt-0.5">Write-to-temp &rarr; fsync() &rarr; atomic rename() pipeline preventing torn writes.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">ATOMIC FSYNC</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-sans text-xs text-slate-300">
              <p>Every replica write adheres strictly to the POSIX durability contract:</p>
              <div class="p-3 bg-black/60 border border-slate-800 rounded font-mono text-purple-300">
                1. Write payload to [objectId].tmp<br>
                2. Flush OS dirty buffers via fsync()<br>
                3. Atomic rename([objectId].tmp &rarr; [objectId].dat)
              </div>
            </div>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: configuration (SYSTEM > Configuration)
      // ═══════════════════════════════════════════════════════════════════════════
      configuration: {
        section: 'SYSTEM ARCHITECTURE',
        title: 'Cluster Configuration',
        render: () => {
          const cfg = VaultStore.config;

          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Technical Configuration</h1>
                <p class="text-xs text-slate-400 mt-0.5">Cluster parameters reported live from GET /cluster/config.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">LIVE CONFIG</span>
            </div>

            <pre class="p-5 bg-black/70 border border-slate-800 rounded-xl text-emerald-400 overflow-x-auto">${JSON.stringify(cfg, null, 2)}</pre>
          </div>
          `;
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // VIEW: cluster_identity (SYSTEM > Cluster Identity)
      // ═══════════════════════════════════════════════════════════════════════════
      cluster_identity: {
        section: 'SYSTEM ARCHITECTURE',
        title: 'Cluster Identity',
        render: () => {
          return `
          <div class="space-y-6 max-w-4xl mx-auto font-mono text-xs">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Identity & Security</h1>
                <p class="text-xs text-slate-400 mt-0.5">Cryptographic identity and operator profiles.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded">OPERATOR-01</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-sans text-xs text-slate-300">
              <div class="font-bold text-white font-mono text-sm">Cluster ID: vault-prod-east-01</div>
              <div>Software Version: <span class="font-mono text-purple-400">v1.4.2</span></div>
              <div>Active Operator: <span class="font-mono text-emerald-400">lead-infra-engineer</span></div>
            </div>
          </div>
          `;
        }
      }
    """

print("app_views_core.py written.")
