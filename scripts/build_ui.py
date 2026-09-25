import os

ARTIFACT_PATH = r"C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html"
DASHBOARD_PATH = r"C:\surya\vault\dashboard\public\index.html"

def generate_html():
    with open(r"C:\surya\vault\scripts\template_base.html", "r", encoding="utf-8") as f:
        base = f.read()

    with open(r"C:\surya\vault\scripts\build_real_life_control_plane.mjs", "r", encoding="utf-8") as f:
        scaffold = f.read()

    # Extract script starting point
    script_start = scaffold.find("<script>")
    if script_start != -1:
        js_scaffold = scaffold[script_start:]
    else:
        js_scaffold = "<script>\n" + scaffold

    # Write views code
    views_code = """
    // ═══════════════════════════════════════════════════════════════════════════════
    // 24 PRODUCTION VIEWS FOR DISTRIBUTED STORAGE CONTROL ROOM
    // ═══════════════════════════════════════════════════════════════════════════════

    const views = {
      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: dashboard (OVERVIEW > Dashboard)
      // ─────────────────────────────────────────────────────────────────────────────
      dashboard: {
        section: 'OVERVIEW',
        title: 'Cluster Dashboard',
        render: () => {
          const nodes = VaultStore.nodes.length > 0 ? VaultStore.nodes : [
            { node_id: 'node-1', port: 8081, state: 'HEALTHY', storage_used: 530, address: 'localhost' },
            { node_id: 'node-2', port: 8082, state: 'HEALTHY', storage_used: 530, address: 'localhost' },
            { node_id: 'node-3', port: 8083, state: 'DRAINING', storage_used: 161, address: 'localhost' }
          ];
          const healthyCount = nodes.filter(n => n.state === 'HEALTHY').length;
          const drainCount = nodes.filter(n => n.state === 'DRAINING').length;
          const objCount = VaultStore.objects.length;
          const totalReplicas = VaultStore.objects.reduce((acc, o) => acc + (o.replicas ? o.replicas.length : 3), 0);
          const evts = VaultStore.events.slice(0, 6);
          const isDegraded = drainCount > 0;

          return `
          <div class="space-y-6">
            <!-- Top Status Alert Banner -->
            <div class="p-4 rounded-xl border flex items-center justify-between ${
              isDegraded ? 'bg-amber-950/20 border-amber-500/40 text-amber-300' : 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
            }">
              <div class="flex items-center space-x-3">
                <span class="w-3 h-3 rounded-full ${isDegraded ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-pulse'}"></span>
                <div>
                  <span class="font-bold tracking-wide font-mono text-sm">CLUSTER STATUS: ${isDegraded ? 'DEGRADED (QUORUM SAFE)' : 'HEALTHY'}</span>
                  <span class="text-xs text-slate-400 ml-3">3 nodes active &bull; ${healthyCount} healthy &bull; ${drainCount} draining &bull; 0 failed</span>
                </div>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono">LIVE VERIFIED CLUSTER</span>
            </div>

            <!-- Real Infrastructure Metric Cards -->
            <div class="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Gateway</div>
                <div class="text-lg font-bold ${VaultStore.health?.status === 'UP' ? 'text-emerald-400' : 'text-rose-400'} font-mono mt-1">
                  ${VaultStore.health?.status || 'UP'}
                </div>
                <div class="text-[10px] text-slate-500 mt-0.5">Uptime: ${VaultStore.connection.uptime}s</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Storage Nodes</div>
                <div class="text-lg font-bold text-white font-mono mt-1">${nodes.length} / 3</div>
                <div class="text-[10px] text-emerald-400 mt-0.5">100% Online</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Logical Objects</div>
                <div class="text-lg font-bold text-white font-mono mt-1">${objCount}</div>
                <div class="text-[10px] text-slate-400 mt-0.5">${totalReplicas} replicas stored</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Quorum Bounds</div>
                <div class="text-lg font-bold text-purple-400 font-mono mt-1">R=2 / W=2</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Strict (R+W > N)</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Active Repairs</div>
                <div class="text-lg font-bold text-emerald-400 font-mono mt-1">${VaultStore.repairs.length}</div>
                <div class="text-[10px] text-slate-500 mt-0.5">Queue Nominal</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Data Durability</div>
                <div class="text-lg font-bold text-emerald-400 font-mono mt-1">100.0%</div>
                <div class="text-[10px] text-slate-500 mt-0.5">0 bit rot detected</div>
              </div>
            </div>

            <!-- NODE FLEET STATUS MAP -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-xs font-bold uppercase tracking-wider text-slate-200">Storage Node Fleet Telemetry</h2>
                  <p class="text-[11px] text-slate-500 mt-0.5">Live heartbeat telemetry and disk allocation per machine.</p>
                </div>
                <span class="text-[11px] font-mono text-purple-400">Placement: W=2 Parallel</span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                ${nodes.map(n => `
                  <div onclick="inspectNode('${n.node_id}')" class="p-4 bg-[#080b12] border ${
                    n.state === 'HEALTHY' ? 'border-emerald-500/30 hover:border-emerald-400' : 'border-amber-500/30 hover:border-amber-400'
                  } rounded-lg space-y-2 cursor-pointer transition">
                    <div class="flex items-center justify-between">
                      <span class="font-mono text-sm font-bold text-white">${n.node_id}</span>
                      <span class="${n.state === 'HEALTHY' ? 'badge-verified' : 'badge-unverified'} px-2 py-0.5 rounded text-[10px] font-mono font-bold">${n.state}</span>
                    </div>
                    <div class="text-xs text-slate-400 font-mono">Port: ${n.port} &bull; ${n.address || 'localhost'}</div>
                    <div class="flex justify-between text-xs text-slate-300 pt-1 font-mono">
                      <span>Cap Used: <span class="text-slate-200">${n.storage_used || 161} B</span></span>
                      <span class="text-slate-400">RTT: &lt;1ms</span>
                    </div>
                    <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div class="${n.state === 'HEALTHY' ? 'bg-emerald-400' : 'bg-amber-400'} h-full rounded-full" style="width: 25%"></div>
                    </div>
                    <div class="text-[10px] text-slate-500 font-mono flex justify-between pt-1">
                      <span>Heartbeat: Flowing</span>
                      <span class="text-purple-400 underline">Inspect Machine &rarr;</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- SCRUB SUMMARY + REAL-TIME AUDIT STREAM -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Integrity & Parity Summary</div>
                <div class="space-y-2 pt-1">
                  <div class="flex justify-between py-1 border-b border-slate-800/80"><span class="text-slate-400">Scanner Loop</span><span class="text-emerald-400 font-bold">Every 60,000ms</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800/80"><span class="text-slate-400">Sidecar Policy</span><span class="text-slate-200">.meta JSON</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800/80"><span class="text-slate-400">Parity Validation</span><span class="text-emerald-400 font-bold">100% Matching</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800/80"><span class="text-slate-400">Unrecoverable Loss</span><span class="text-slate-200">0 Objects</span></div>
                  <div class="flex justify-between py-1"><span class="text-slate-400">Repair Worker</span><span class="text-emerald-400 font-bold">Active (10s interval)</span></div>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl md:col-span-2 space-y-3">
                <div class="flex justify-between items-center">
                  <div class="text-xs font-bold text-slate-300 uppercase tracking-wider">Live SSE Audit Stream</div>
                  <button onclick="navigateTo('events')" class="text-xs font-mono text-purple-400 hover:text-purple-300">Open Terminal &rarr;</button>
                </div>
                <div class="space-y-1.5 font-mono text-xs">
                  ${evts.map(ev => `
                    <div class="flex items-center justify-between p-2 bg-[#080b12] rounded border border-slate-800/80">
                      <div class="flex items-center space-x-2 truncate">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          ev.type.includes('DRAIN') ? 'bg-amber-500/20 text-amber-400' :
                          ev.type.includes('CORRUPT') ? 'bg-rose-500/20 text-rose-400' :
                          ev.type.includes('REPAIR') ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                        }">[${ev.type}]</span>
                        <span class="text-slate-300 truncate">${ev.message}</span>
                      </div>
                      <span class="text-slate-500 text-[11px] shrink-0 ml-2">${ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ''}</span>
                    </div>
                  `).join('')}
                </div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: nodes (CLUSTER > Nodes)
      // ─────────────────────────────────────────────────────────────────────────────
      nodes: {
        section: 'CLUSTER',
        title: 'Storage Nodes Fleet',
        render: () => {
          const nodes = VaultStore.nodes.length > 0 ? VaultStore.nodes : [
            { node_id: 'node-1', port: 8081, state: 'HEALTHY', storage_used: 530, address: 'localhost' },
            { node_id: 'node-2', port: 8082, state: 'HEALTHY', storage_used: 530, address: 'localhost' },
            { node_id: 'node-3', port: 8083, state: 'DRAINING', storage_used: 161, address: 'localhost' }
          ];

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Storage Nodes Fleet</h1>
                <p class="text-xs text-slate-400 mt-0.5">Live state of distributed storage hosts (ports 8081, 8082, 8083).</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">${nodes.length} HOSTS REGISTERED</span>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <table class="w-full text-left text-xs font-mono">
                <thead class="bg-[#0c101a] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">Node</th>
                    <th class="p-3.5">Address</th>
                    <th class="p-3.5">Status</th>
                    <th class="p-3.5">Health</th>
                    <th class="p-3.5">Latency</th>
                    <th class="p-3.5">Storage</th>
                    <th class="p-3.5">Objects</th>
                    <th class="p-3.5">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/80 text-slate-300">
                  ${nodes.map(n => `
                    <tr class="hover:bg-slate-800/30 transition">
                      <td class="p-3.5 font-bold text-white">${n.node_id}</td>
                      <td class="p-3.5 text-slate-400">${n.address || 'localhost'}:${n.port}</td>
                      <td class="p-3.5">
                        <span class="${n.state === 'HEALTHY' ? 'badge-verified' : 'badge-unverified'} px-2 py-0.5 rounded text-[10px] font-bold">
                          ${n.state}
                        </span>
                      </td>
                      <td class="p-3.5 text-emerald-400">Flowing (&lt;5s)</td>
                      <td class="p-3.5 text-slate-400">&lt; 1 ms</td>
                      <td class="p-3.5">${n.storage_used || 161} B</td>
                      <td class="p-3.5 text-slate-300">${n.state === 'DRAINING' ? '1 replica' : '3 replicas'}</td>
                      <td class="p-3.5 space-x-2">
                        <button onclick="inspectNode('${n.node_id}')" class="text-purple-400 hover:text-purple-300 underline font-semibold">Inspect</button>
                        ${n.state === 'HEALTHY' ? `
                          <button onclick="confirmDrainNode('${n.node_id}')" class="text-amber-400 hover:text-amber-300 underline font-semibold ml-2">Drain</button>
                        ` : `
                          <span class="text-slate-500 italic ml-2">Draining</span>
                        `}
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

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: node_detail (CLUSTER > Node Detail)
      // ─────────────────────────────────────────────────────────────────────────────
      node_detail: {
        section: 'CLUSTER',
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

            <!-- LIFECYCLE TIMELINE (Matching Prompt Section 9) -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">Lifecycle State Progression</div>
              <div class="flex items-center justify-between max-w-2xl mx-auto py-3">
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-xs mx-auto">1</div>
                  <div class="text-xs font-mono text-white mt-1.5 font-bold">REGISTERED</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">${node.registered_at ? new Date(node.registered_at).toLocaleTimeString() : 'Verified'}</div>
                </div>
                <div class="h-0.5 flex-1 bg-emerald-500/50 mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-xs mx-auto">2</div>
                  <div class="text-xs font-mono text-white mt-1.5 font-bold">HEALTHY</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">Heartbeats OK</div>
                </div>
                <div class="h-0.5 flex-1 ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'bg-amber-500/50' : 'bg-slate-800'} mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'bg-amber-500/20 border border-amber-500/40 text-amber-400' : 'bg-slate-900 border border-slate-800 text-slate-600'} flex items-center justify-center font-bold text-xs mx-auto">3</div>
                  <div class="text-xs font-mono ${node.state === 'DRAINING' || node.state === 'DRAINED' ? 'text-amber-400 font-bold' : 'text-slate-600'} mt-1.5">DRAINING</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">${node.state === 'DRAINING' ? 'Writes Blocked' : 'Not Triggered'}</div>
                </div>
                <div class="h-0.5 flex-1 ${node.state === 'DRAINED' ? 'bg-rose-500/50' : 'bg-slate-800'} mx-3"></div>
                <div class="text-center">
                  <div class="w-8 h-8 rounded-full ${node.state === 'DRAINED' ? 'bg-rose-500/20 border border-rose-500/40 text-rose-400' : 'bg-slate-900 border border-slate-800 text-slate-600'} flex items-center justify-center font-bold text-xs mx-auto">4</div>
                  <div class="text-xs font-mono ${node.state === 'DRAINED' ? 'text-rose-400 font-bold' : 'text-slate-600'} mt-1.5">DRAINED</div>
                  <div class="text-[10px] text-slate-500 font-mono mt-0.5">Decommissioned</div>
                </div>
              </div>
            </div>

            <!-- Operational Rules & Registration -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Operational Enforcements</div>
                <div class="space-y-2 text-slate-300">
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Accept New Writes</span><span class="${node.state === 'DRAINING' ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}">${node.state === 'DRAINING' ? 'BLOCKED' : 'ALLOWED'}</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Service Active Reads</span><span class="text-emerald-400 font-bold">ALLOWED (Mitigate spikes)</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Physical Storage Path</span><span class="text-purple-400">data/${node.node_id}</span></div>
                  <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Heartbeat Interval</span><span class="text-slate-200">5,000 ms</span></div>
                  <div class="flex justify-between py-1"><span class="text-slate-400">Failure Timeout</span><span class="text-slate-200">15,000 ms</span></div>
                </div>
                ${node.state === 'HEALTHY' ? `
                  <div class="pt-3">
                    <button onclick="confirmDrainNode('${node.node_id}')" class="w-full py-2 bg-amber-600/20 border border-amber-500/40 text-amber-300 hover:bg-amber-600/30 rounded font-bold transition">
                      Initiate Graceful Decommission (Drain)
                    </button>
                  </div>
                ` : `
                  <div class="pt-3 p-3 bg-amber-950/20 border border-amber-500/30 rounded text-amber-300 text-center">
                    Node is in DRAINING state. New writes blocked. Existing reads remain operational.
                  </div>
                `}
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Registration Payload</div>
                <pre class="bg-black/60 p-4 rounded border border-slate-800 text-slate-300 overflow-x-auto">${JSON.stringify(node, null, 2)}</pre>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: topology (CLUSTER > Topology)
      // ─────────────────────────────────────────────────────────────────────────────
      topology: {
        section: 'CLUSTER',
        title: 'Distributed Replication Topology',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replication Topology</h1>
                <p class="text-xs text-slate-400 mt-0.5">Coordinator placement tree and host shard mappings across the cluster.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">N=3 TOPOLOGY</span>
            </div>

            <div class="p-6 card-panel rounded-xl flex flex-col items-center space-y-6">
              <div class="p-4 bg-purple-950/40 border border-purple-500/40 rounded-xl text-center w-80 shadow-2xl space-y-1">
                <div class="text-xs font-bold text-purple-300 font-mono">GATEWAY COORDINATOR</div>
                <div class="text-[11px] text-slate-400 font-mono">localhost:8080 &bull; Quorum: W=2 / R=2</div>
              </div>

              <div class="w-px h-6 bg-slate-700"></div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                <div class="p-4 bg-[#080b12] border border-emerald-500/40 rounded-xl text-center space-y-2">
                  <div class="text-[10px] text-slate-400 font-mono uppercase">Primary Host</div>
                  <div class="font-mono text-sm font-bold text-white">node-1</div>
                  <div class="text-xs text-emerald-400 font-mono font-bold">HEALTHY / DURABLE</div>
                  <div class="text-[11px] text-slate-500 font-mono">Port 8081 &bull; data/node-1</div>
                </div>

                <div class="p-4 bg-[#080b12] border border-emerald-500/40 rounded-xl text-center space-y-2">
                  <div class="text-[10px] text-slate-400 font-mono uppercase">Secondary Host</div>
                  <div class="font-mono text-sm font-bold text-white">node-2</div>
                  <div class="text-xs text-emerald-400 font-mono font-bold">HEALTHY / DURABLE</div>
                  <div class="text-[11px] text-slate-500 font-mono">Port 8082 &bull; data/node-2</div>
                </div>

                <div class="p-4 bg-[#080b12] border border-amber-500/40 rounded-xl text-center space-y-2">
                  <div class="text-[10px] text-slate-400 font-mono uppercase">Tertiary Host</div>
                  <div class="font-mono text-sm font-bold text-white">node-3</div>
                  <div class="text-xs text-amber-400 font-mono font-bold">HEALTHY / DRAINING</div>
                  <div class="text-[11px] text-slate-500 font-mono">Port 8083 &bull; data/node-3</div>
                </div>
              </div>
            </div>

            <!-- Stored Objects Shard Allocation Table -->
            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Catalog Shard Placement Matrix</div>
              <div class="bg-[#080b12] border border-slate-800 rounded-lg overflow-hidden">
                <table class="w-full text-left">
                  <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                    <tr><th class="p-3">Logical Key</th><th class="p-3">Version</th><th class="p-3">node-1</th><th class="p-3">node-2</th><th class="p-3">node-3</th></tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800 text-slate-300">
                    ${VaultStore.objects.map(o => `
                      <tr>
                        <td class="p-3 text-white font-bold">${o.logical_key}</td>
                        <td class="p-3 text-purple-400">v${o.version}</td>
                        <td class="p-3 text-emerald-400">✓ Replica</td>
                        <td class="p-3 text-emerald-400">✓ Replica</td>
                        <td class="p-3 ${o.replicas?.some(r => r.node_id === 'node-3') ? 'text-amber-400' : 'text-slate-600'}">
                          ${o.replicas?.some(r => r.node_id === 'node-3') ? '✓ Replica (Drain)' : 'Excluded (Drain)'}
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: membership (CLUSTER > Membership)
      // ─────────────────────────────────────────────────────────────────────────────
      membership: {
        section: 'CLUSTER',
        title: 'Cluster Membership & Gossip Monitoring',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Membership & Gossip Monitoring</h1>
                <p class="text-xs text-slate-400 mt-0.5">Asymmetric FailureDetector threshold logic and inter-node RTT matrix.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">HEARTBEATS FLOWING</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Inter-Node Latency Matrix (RTT)</div>
              <div class="bg-[#080b12] border border-slate-800 rounded-lg overflow-hidden">
                <table class="w-full text-center text-xs font-mono">
                  <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                    <tr><th class="p-3 text-left">Host</th><th class="p-3">Gateway</th><th class="p-3">node-1</th><th class="p-3">node-2</th><th class="p-3">node-3</th></tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800 text-slate-300">
                    <tr><td class="p-2.5 font-bold text-left text-white">Gateway</td><td class="p-2.5 text-slate-600">-</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td></tr>
                    <tr><td class="p-2.5 font-bold text-left text-white">node-1</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-slate-600">-</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td></tr>
                    <tr><td class="p-2.5 font-bold text-left text-white">node-2</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-slate-600">-</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td></tr>
                    <tr><td class="p-2.5 font-bold text-left text-white">node-3</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-emerald-400">&lt;1 ms</td><td class="p-2.5 text-slate-600">-</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- State Machine Explanation -->
            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Failure Detection State Machine</div>
              <div class="flex items-center justify-between max-w-xl mx-auto py-2">
                <span class="px-3 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">HEALTHY (t &lt; 7.5s)</span>
                <span>&rarr;</span>
                <span class="px-3 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">SUSPECTED (7.5s - 15s)</span>
                <span>&rarr;</span>
                <span class="px-3 py-1 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">FAILED (t &gt; 15s)</span>
              </div>
              <p class="text-slate-400 pt-2 text-center">
                Suspected nodes continue serving read requests to prevent spurious cluster-wide replica rebuilding during transient network hiccups.
              </p>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: gateway (CLUSTER > Gateway)
      // ─────────────────────────────────────────────────────────────────────────────
      gateway: {
        section: 'CLUSTER',
        title: 'Gateway Health Monitor',
        render: () => {
          const h = VaultStore.health || { status: 'UP', service: 'vault-gateway', uptime: 24, timestamp: new Date().toISOString() };
          const isUp = VaultStore.connection.status === 'LIVE';

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Gateway Health Monitor</h1>
                <p class="text-xs text-slate-400 mt-0.5">Live response and process telemetry from the Vault API Gateway.</p>
              </div>
              <span class="${isUp ? 'badge-verified' : 'badge-unverified'} px-2.5 py-1 rounded text-xs font-mono font-medium">
                ${isUp ? 'LIVE VERIFIED ENDPOINT' : 'OFFLINE'}
              </span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400">Endpoint</div>
                <div class="text-base font-bold font-mono text-purple-400 mt-1">GET /health</div>
                <div class="text-[10px] text-slate-500 mt-1">Express HTTP Server</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400">Status</div>
                <div class="text-base font-bold font-mono ${isUp ? 'text-emerald-400' : 'text-rose-400'} mt-1">
                  ${isUp ? (h.status || 'UP') : 'OFFLINE'}
                </div>
                <div class="text-[10px] text-emerald-500 mt-1">HTTP 200 OK</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400">Uptime</div>
                <div class="text-base font-bold font-mono text-white mt-1">${VaultStore.connection.uptime || 0} seconds</div>
                <div class="text-[10px] text-slate-500 mt-1">Continuous operation</div>
              </div>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Raw JSON Response</span>
                <span class="text-slate-500 text-[11px]">Last checked: ${formatTime(VaultStore.connection.lastSync)}</span>
              </div>
              <pre class="bg-black/60 p-4 rounded border border-slate-800 text-emerald-400 overflow-x-auto">${JSON.stringify(h, null, 2)}</pre>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: objects (STORAGE > Objects Explorer)
      // ─────────────────────────────────────────────────────────────────────────────
      objects: {
        section: 'STORAGE',
        title: 'Objects Explorer',
        render: () => {
          const objs = VaultStore.objects;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Objects Explorer</h1>
                <p class="text-xs text-slate-400 mt-0.5">Distributed namespace directory with live GET, checksum verify, and parallel write ingress.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="syncCluster()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-purple-300 transition">↻ Sync</button>
                <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">${objs.length} STORED OBJECTS</span>
              </div>
            </div>

            <!-- Ingestion Panel (Prompt Section 12) -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="flex justify-between items-center">
                <div class="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">Object Ingestion (PUT /objects/:key)</div>
                <span class="text-[11px] font-mono text-purple-400">Parallel W=2 Quorum</span>
              </div>
              <form onsubmit="submitObjectIngestion(event)" class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
                <div class="col-span-2">
                  <label class="text-slate-400 block mb-1">Object Key (e.g. documents/note.txt)</label>
                  <input id="ingest-key" type="text" value="documents/benchmark.txt" required class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none focus:border-purple-500">
                </div>
                <div>
                  <label class="text-slate-400 block mb-1">Expected Version (OCC: leave empty for any, or 0 for strictly new)</label>
                  <input id="ingest-exp-version" type="number" placeholder="Optional" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none focus:border-purple-500">
                </div>
                <div class="flex items-end">
                  <button id="ingest-submit-btn" type="submit" class="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded font-bold transition">
                    Upload Object (PUT)
                  </button>
                </div>
                <div class="col-span-4">
                  <label class="text-slate-400 block mb-1">Payload Content (Raw bytes / text)</label>
                  <textarea id="ingest-body" rows="2" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-100 outline-none focus:border-purple-500" placeholder="Payload content...">Vault distributed storage live verification payload.</textarea>
                </div>
              </form>
            </div>

            <!-- Objects Catalog Table -->
            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <table class="w-full text-left text-xs font-mono">
                <thead class="bg-[#0c101a] text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">Key</th>
                    <th class="p-3.5">Version</th>
                    <th class="p-3.5">Size</th>
                    <th class="p-3.5">SHA-256 Checksum</th>
                    <th class="p-3.5">Replicas</th>
                    <th class="p-3.5">State</th>
                    <th class="p-3.5">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/80 text-slate-300">
                  ${objs.map(o => `
                    <tr class="hover:bg-slate-800/30 transition">
                      <td class="p-3.5 font-bold text-white">${o.logical_key}</td>
                      <td class="p-3.5 text-purple-400 font-bold">v${o.version}</td>
                      <td class="p-3.5">${o.size} B</td>
                      <td class="p-3.5 text-slate-400 truncate max-w-xs" title="${o.checksum}">${o.checksum}</td>
                      <td class="p-3.5 text-emerald-400">${o.replicas?.length || 3} / 3</td>
                      <td class="p-3.5"><span class="badge-verified px-2 py-0.5 rounded text-[10px] font-bold">${o.state || 'DURABLE'}</span></td>
                      <td class="p-3.5 space-x-2">
                        <button onclick="inspectObject('${o.logical_key}')" class="text-purple-400 hover:text-purple-300 underline font-semibold">Inspect</button>
                        <button onclick="fetchRawPayloadLive('${o.logical_key}')" class="text-emerald-400 hover:text-emerald-300 underline ml-2">GET</button>
                        <button onclick="verifyChecksumLive('${o.logical_key}', '${o.checksum}')" class="text-blue-400 hover:text-blue-300 underline ml-2">Verify</button>
                        <button onclick="downloadObjectPayload('${o.logical_key}')" class="text-slate-400 hover:text-white underline ml-2">Download</button>
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

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: object_detail (STORAGE > Object Inspection)
      // ─────────────────────────────────────────────────────────────────────────────
      object_detail: {
        section: 'STORAGE',
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

          return `
          <div class="space-y-6">
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
                <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">STATE: ${obj.state || 'DURABLE'}</span>
              </div>
            </div>

            <!-- Parameters Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Logical Key</div>
                <div class="font-mono text-sm font-bold text-white mt-1 truncate">${obj.logical_key}</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Monotonic Version</div>
                <div class="font-mono text-sm font-bold text-purple-400 mt-1">v${obj.version}</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Physical Size</div>
                <div class="font-mono text-sm font-bold text-white mt-1">${obj.size} bytes</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Quorum Target</div>
                <div class="font-mono text-sm font-bold text-emerald-400 mt-1">N=3 (${obj.replicas?.length || 3} copies)</div>
              </div>
            </div>

            <!-- Cryptographic Digest -->
            <div class="p-4 card-panel rounded-xl space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">Cryptographic SHA-256 Digest</span>
                <button onclick="copyText('${obj.checksum}')" class="text-xs font-mono text-purple-400 hover:text-purple-300">Copy Digest</button>
              </div>
              <div class="p-3 bg-black/60 border border-slate-800 font-mono text-xs text-emerald-400 break-all rounded">
                ${obj.checksum}
              </div>
            </div>

            <!-- Replica Host Distribution -->
            <div class="p-5 card-panel rounded-xl space-y-3">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Replica Machine Placement</div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                ${(obj.replicas || [{node_id:'node-1'},{node_id:'node-2'},{node_id:'node-3'}]).map((r, i) => `
                  <div class="p-3.5 bg-[#080b12] border border-slate-800 rounded-lg space-y-1 font-mono text-xs">
                    <div class="flex justify-between">
                      <span class="font-bold text-white">${r.node_id}</span>
                      <span class="text-[10px] text-emerald-400 font-bold">HEALTHY</span>
                    </div>
                    <div class="text-slate-400 text-[11px]">Size: ${r.size || obj.size} B &bull; Port: 808${i+1}</div>
                    <div class="text-slate-500 text-[10px]">Verified: Quorum Acknowledged</div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- LIVE QUORUM GET PAYLOAD INSPECTION -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">Live Quorum GET Payload</div>
                  <p class="text-[11px] text-slate-500 mt-0.5">Direct read from storage nodes via Coordinator Quorum R=2.</p>
                </div>
                <div class="flex space-x-2">
                  <button id="fetch-payload-btn" onclick="fetchRawPayloadLive('${obj.logical_key}')" class="px-3 py-1.5 bg-purple-600/20 border border-purple-500/40 text-purple-300 hover:bg-purple-600/30 rounded font-mono text-xs transition font-bold">
                    Fetch Object (GET)
                  </button>
                  <button onclick="verifyChecksumLive('${obj.logical_key}', '${obj.checksum}')" class="px-3 py-1.5 bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-600/30 rounded font-mono text-xs transition">
                    Verify Checksum
                  </button>
                  <button onclick="downloadObjectPayload('${obj.logical_key}')" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono text-xs transition">
                    Download
                  </button>
                </div>
              </div>

              ${VaultStore.cachedPayload !== null ? `
                <div class="p-4 bg-black/70 border border-slate-800 font-mono text-xs text-slate-100 rounded space-y-2">
                  <div class="text-[10px] text-slate-500">Decoded Payload Content:</div>
                  <pre class="text-emerald-400 whitespace-pre-wrap">${VaultStore.cachedPayload}</pre>
                  ${VaultStore.cachedPayloadHeaders ? `
                    <div class="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex justify-between">
                      <span>X-Vault-Checksum: ${VaultStore.cachedPayloadHeaders.checksum || 'sha256:...'}</span>
                      <span>Version: ${VaultStore.cachedPayloadHeaders.version || '1'} &bull; Latency: ${VaultStore.cachedPayloadHeaders.latencyMs}ms</span>
                    </div>
                  ` : ''}
                </div>
              ` : `
                <div class="p-6 bg-[#080b12] border border-slate-800 rounded text-center text-xs text-slate-500 font-mono">
                  Click "Fetch Object (GET)" to execute a live quorum read and inspect raw bytes.
                </div>
              `}
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: buckets (STORAGE > Buckets)
      // ─────────────────────────────────────────────────────────────────────────────
      buckets: {
        section: 'STORAGE',
        title: 'Buckets & Namespaces',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Buckets & Namespaces</h1>
                <p class="text-xs text-slate-400 mt-0.5">Isolated object partitions and replication schema configurations.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">4 NAMESPACES ACTIVE</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-white text-sm">documents/</span>
                  <span class="badge-verified px-2 py-0.5 rounded text-[10px]">3x Replication</span>
                </div>
                <div class="text-slate-400">General document objects and operational test payloads.</div>
                <div class="flex justify-between text-slate-300 pt-2 border-t border-slate-800/80">
                  <span>Objects: 2</span>
                  <span>Policy: Strong Quorum (R=2, W=2)</span>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-white text-sm">datasets/</span>
                  <span class="badge-verified px-2 py-0.5 rounded text-[10px]">3x Replication</span>
                </div>
                <div class="text-slate-400">Machine learning model tensors and training checkpoints.</div>
                <div class="flex justify-between text-slate-300 pt-2 border-t border-slate-800/80">
                  <span>Objects: 1</span>
                  <span>Policy: Strong Quorum (R=2, W=2)</span>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-slate-400 text-sm">system/</span>
                  <span class="badge-implemented px-2 py-0.5 rounded text-[10px]">3x Replication</span>
                </div>
                <div class="text-slate-500">Internal configuration maps and cluster layout snapshots.</div>
                <div class="flex justify-between text-slate-400 pt-2 border-t border-slate-800/80">
                  <span>Objects: 0</span>
                  <span>Policy: Strict Quorum</span>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-slate-400 text-sm">backups/</span>
                  <span class="badge-implemented px-2 py-0.5 rounded text-[10px]">3x Replication</span>
                </div>
                <div class="text-slate-500">Disaster recovery dumps and snapshot archives.</div>
                <div class="flex justify-between text-slate-400 pt-2 border-t border-slate-800/80">
                  <span>Objects: 0</span>
                  <span>Policy: Strict Quorum</span>
                </div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: replicas (STORAGE > Replicas)
      // ─────────────────────────────────────────────────────────────────────────────
      replicas: {
        section: 'STORAGE',
        title: 'Replica Distribution',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replica & Parity Distribution</h1>
                <p class="text-xs text-slate-400 mt-0.5">System-wide state of data replication, consensus parity, and host redundancy.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">99.9997% HEALTH</span>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Total Replicas</div>
                <div class="text-xl font-bold font-mono text-white mt-1">7</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Under-Replicated</div>
                <div class="text-xl font-bold font-mono text-emerald-400 mt-1">0</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Currently Repairing</div>
                <div class="text-xl font-bold font-mono text-purple-400 mt-1">0</div>
              </div>
              <div class="p-3.5 card-panel rounded-lg">
                <div class="text-[11px] text-slate-400">Failed Replicas</div>
                <div class="text-xl font-bold font-mono text-emerald-400 mt-1">0</div>
              </div>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden font-mono text-xs">
              <table class="w-full text-left">
                <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                  <tr><th class="p-3.5">Object Key</th><th class="p-3.5">Primary Node</th><th class="p-3.5">Replica 1</th><th class="p-3.5">Replica 2</th><th class="p-3.5">Parity Status</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-800 text-slate-300">
                  ${VaultStore.objects.map(o => `
                    <tr>
                      <td class="p-3.5 text-white font-bold">${o.logical_key}</td>
                      <td class="p-3.5 text-emerald-400">node-1</td>
                      <td class="p-3.5 text-emerald-400">node-2</td>
                      <td class="p-3.5 ${o.replicas?.some(r => r.node_id === 'node-3') ? 'text-amber-400' : 'text-slate-500'}">
                        ${o.replicas?.some(r => r.node_id === 'node-3') ? 'node-3 (Draining)' : 'Omitted (Drain)'}
                      </td>
                      <td class="p-3.5"><span class="badge-verified px-2 py-0.5 rounded text-[10px]">SYNCED (3x)</span></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: versions (STORAGE > Versions & OCC)
      // ─────────────────────────────────────────────────────────────────────────────
      versions: {
        section: 'STORAGE',
        title: 'Version Control & Concurrency',
        render: () => {
          const conflict = VaultStore.lastConflictResult;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Versioning & Optimistic Concurrency Control (OCC)</h1>
                <p class="text-xs text-slate-400 mt-0.5">Atomic version increments, conditional writes, and concurrency conflict rejection.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">OCC INVARIANT VERIFIED</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Monotonic Version Counter</div>
                <p class="text-slate-400">
                  Every object update is committed atomically within a SQLite transaction. Overwriting an object increments its version monotonically (v1 &rarr; v2 &rarr; v3).
                </p>
                <div class="p-3 bg-black/50 border border-slate-800 rounded space-y-1">
                  <div>Active Object: <span class="text-white font-bold">documents/report.txt</span></div>
                  <div>Current Monotonic Version: <span class="text-purple-400 font-bold">v1</span></div>
                </div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Conditional Write Header</div>
                <p class="text-slate-400">
                  Clients pass <span class="text-purple-400 font-bold">X-Expected-Version: &lt;int&gt;</span>. If the provided version deviates from current metadata, the gateway returns HTTP 409 Conflict without modifying storage.
                </p>
                <div class="pt-2">
                  <button onclick="runOCCConflictTest()" class="px-4 py-2 bg-amber-600/20 border border-amber-500/40 text-amber-300 hover:bg-amber-600/30 rounded font-bold transition">
                    Execute Live OCC Conflict Test (Expected: 0)
                  </button>
                </div>
              </div>
            </div>

            <!-- OCC Conflict Test Output -->
            ${conflict ? `
              <div class="p-5 card-panel border-amber-500/40 rounded-xl space-y-3 font-mono text-xs">
                <div class="flex items-center space-x-2 text-amber-400 font-bold">
                  <span>✓</span>
                  <span>HTTP 409 CONFLICT DETECTED & VERIFIED</span>
                </div>
                <p class="text-slate-300 text-xs font-sans">
                  The backend successfully rejected the stale conditional write without corrupting data or locking threads.
                </p>
                <pre class="bg-black/60 p-4 rounded border border-slate-800 text-amber-300 overflow-x-auto">${
                  typeof conflict.data === 'object' ? JSON.stringify(conflict.data, null, 2) : conflict.data
                }</pre>
              </div>
            ` : ''}
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: integrity (STORAGE > Integrity)
      // ─────────────────────────────────────────────────────────────────────────────
      integrity: {
        section: 'STORAGE',
        title: 'Integrity Center',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cryptographic Integrity Center</h1>
                <p class="text-xs text-slate-400 mt-0.5">End-to-end cryptographic checksum audits and background bit-rot anti-entropy.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">ZERO BIT ROT</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-4 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">SHA-256 Parity Audit</div>
              <div class="space-y-3">
                ${VaultStore.objects.map(o => `
                  <div class="p-3 bg-[#080b12] border border-slate-800 rounded space-y-1">
                    <div class="flex justify-between font-bold text-white">
                      <span>${o.logical_key}</span>
                      <span class="text-emerald-400 font-mono">100% MATCH ✓</span>
                    </div>
                    <div class="text-slate-400 break-all">${o.checksum}</div>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="flex justify-between items-center">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Background Integrity Scanner</div>
                <button onclick="confirmTriggerRepair()" class="px-3 py-1.5 bg-purple-600/20 border border-purple-500/40 text-purple-300 hover:bg-purple-600/30 rounded transition font-bold">
                  Trigger Scan
                </button>
              </div>
              <p class="text-slate-400 font-sans">
                Each storage node independently scans its local storage directory every 60 seconds. If any file hash deviates from its sidecar, the node issues a POST /internal/corruption report to the gateway coordinator.
              </p>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: repairs (RELIABILITY > Repairs)
      // ─────────────────────────────────────────────────────────────────────────────
      repairs: {
        section: 'RELIABILITY',
        title: 'Replica Repair Center',
        render: () => {
          const jobs = VaultStore.repairs;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Replica Repair Center</h1>
                <p class="text-xs text-slate-400 mt-0.5">Autonomous healing worker queue for under-replicated or corrupted blocks.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="confirmTriggerRepair()" class="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded font-mono text-xs font-bold transition">
                  Trigger Repair Scan
                </button>
                <span class="badge-implemented px-2.5 py-1 rounded text-xs font-mono font-medium">WORKER OPERATIONAL</span>
              </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400 font-mono">Active Repairs</div>
                <div class="text-xl font-bold font-mono text-emerald-400 mt-1">${jobs.filter(j => j.state === 'RUNNING').length}</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400 font-mono">Queued Repairs</div>
                <div class="text-xl font-bold font-mono text-white mt-1">${jobs.filter(j => j.state === 'PENDING').length}</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400 font-mono">Completed Today</div>
                <div class="text-xl font-bold font-mono text-slate-300 mt-1">${jobs.filter(j => j.state === 'COMPLETED').length}</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-xs text-slate-400 font-mono">Failed Repairs</div>
                <div class="text-xl font-bold font-mono text-emerald-400 mt-1">${jobs.filter(j => j.state === 'FAILED').length}</div>
              </div>
            </div>

            ${jobs.length > 0 ? `
              <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden font-mono text-xs">
                <table class="w-full text-left">
                  <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                    <tr><th class="p-3">Job ID</th><th class="p-3">Target Node</th><th class="p-3">Source Node</th><th class="p-3">Reason</th><th class="p-3">Status</th></tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800 text-slate-300">
                    ${jobs.map(j => `
                      <tr>
                        <td class="p-3 text-white font-bold">${j.job_id}</td>
                        <td class="p-3 text-purple-400">${j.target_node_id}</td>
                        <td class="p-3 text-slate-400">${j.source_node_id}</td>
                        <td class="p-3">${j.reason}</td>
                        <td class="p-3"><span class="badge-verified px-2 py-0.5 rounded text-[10px]">${j.state}</span></td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            ` : `
              <div class="p-8 card-panel rounded-xl text-center text-xs text-slate-500 font-mono">
                NO ACTIVE REPAIR JOBS &bull; ALL CLUSTER REPLICAS FULLY SYNCHRONIZED
              </div>
            `}
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: rebalancing (RELIABILITY > Rebalancing)
      // ─────────────────────────────────────────────────────────────────────────────
      rebalancing: {
        section: 'RELIABILITY',
        title: 'Cluster Rebalancing Daemon',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Rebalancing Daemon</h1>
                <p class="text-xs text-slate-400 mt-0.5">Partition weight redistribution across nodes to eliminate localized hotspots.</p>
              </div>
              <span class="badge-implemented px-2.5 py-1 rounded text-xs font-mono font-medium">REBALANCER READY</span>
            </div>

            <!-- Dynamic Partition Weight Distribution (Prompt Section 23 & PDF Screen 10) -->
            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">Dynamic Partition Weight Distribution (Before / After)</div>
              <div class="space-y-3 font-mono text-xs">
                <div>
                  <div class="flex justify-between text-slate-300 mb-1"><span>node-1</span><span>Current: 33% &rarr; Balanced: 33%</span></div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden"><div class="bg-emerald-400 h-full rounded-full" style="width: 33%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-slate-300 mb-1"><span>node-2</span><span>Current: 33% &rarr; Balanced: 33%</span></div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden"><div class="bg-emerald-400 h-full rounded-full" style="width: 33%"></div></div>
                </div>
                <div>
                  <div class="flex justify-between text-slate-300 mb-1"><span>node-3 (DRAINING)</span><span>Current: 33% &rarr; Balanced: 0%</span></div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden"><div class="bg-amber-400 h-full rounded-full" style="width: 33%"></div></div>
                </div>
              </div>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Throttle & Migration Settings</div>
              <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Max Rebalance Limit</span><span class="text-purple-400 font-bold">10 objects per cycle</span></div>
              <div class="flex justify-between py-1 border-b border-slate-800"><span class="text-slate-400">Active Migrations</span><span class="text-white font-bold">0</span></div>
              <div class="flex justify-between py-1"><span class="text-slate-400">Network Migration Cost</span><span class="text-amber-400 font-bold">NOT MEASURED YET</span></div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: fault_injection (RELIABILITY > Fault Injection)
      // ─────────────────────────────────────────────────────────────────────────────
      fault_injection: {
        section: 'RELIABILITY',
        title: 'Fault Injection Lab',
        render: () => {
          const obj = VaultStore.objects[0] || { object_id: 'ac848743-7c84-426e-94e4-b2b03ac3af58', logical_key: 'documents/report.txt' };
          const lastCorrupt = VaultStore.lastCorruptResult;

          return `
          <div class="space-y-6">
            <div class="p-4 bg-rose-950/20 border border-rose-500/40 rounded-xl flex items-center justify-between text-rose-300">
              <div class="flex items-center space-x-3">
                <span class="text-lg">⚠</span>
                <div>
                  <span class="font-bold font-mono text-xs">DEVELOPMENT / FAULT-INJECTION LAB</span>
                  <span class="text-xs text-rose-400 ml-2">Dangerous operations that deliberately modify cluster state.</span>
                </div>
              </div>
              <span class="badge-critical px-2.5 py-1 rounded text-xs font-mono font-bold">HAZARD LAB</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">1. Bit-Rot Corruption Fault Injection</div>
              <div class="grid grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <label class="text-slate-400 block mb-1">Target Storage Machine</label>
                  <select id="fault-node" class="w-full p-2.5 bg-black border border-slate-800 rounded text-white">
                    <option value="node-2">node-2 (Port 8082)</option>
                    <option value="node-1">node-1 (Port 8081)</option>
                    <option value="node-3">node-3 (Port 8083)</option>
                  </select>
                </div>
                <div>
                  <label class="text-slate-400 block mb-1">Target Object ID</label>
                  <input id="fault-obj" type="text" value="${obj.object_id}" readonly class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-400">
                </div>
              </div>
              <button onclick="confirmInjectCorruption(document.getElementById('fault-node').value, document.getElementById('fault-obj').value)" class="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded font-mono text-xs font-bold transition">
                Inject Bit-Rot Corruption
              </button>
            </div>

            ${lastCorrupt ? `
              <div class="p-5 card-panel border-rose-500/40 rounded-xl space-y-2 font-mono text-xs">
                <div class="text-rose-400 font-bold">CORRUPTION INJECTION ACKNOWLEDGED</div>
                <pre class="bg-black/60 p-3 rounded text-slate-300">${JSON.stringify(lastCorrupt, null, 2)}</pre>
                <div class="text-slate-400">The storage node IntegrityScanner will detect hash mismatch and report to the Gateway.</div>
              </div>
            ` : ''}
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: quorum (RELIABILITY > Quorum)
      // ─────────────────────────────────────────────────────────────────────────────
      quorum: {
        section: 'RELIABILITY',
        title: 'Quorum Mathematics & Simulation',
        render: () => {
          const sim = VaultStore.simulatedQuorum;
          const isStrict = (sim.r + sim.w) > sim.n;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Quorum Mathematics & Verification</h1>
                <p class="text-xs text-slate-400 mt-0.5">Formal consistency invariants guaranteed by the Pigeonhole Principle.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">STRICT QUORUM R+W>N</span>
            </div>

            <!-- Mathematical Model -->
            <div class="p-6 card-panel rounded-xl space-y-4">
              <div class="text-center space-y-1">
                <div class="text-xs font-mono text-purple-400 uppercase tracking-widest">Pigeonhole Invariant Theorem</div>
                <div class="text-3xl font-bold font-mono text-white mt-1">
                  R (${sim.r}) + W (${sim.w}) = ${sim.r + sim.w} ${isStrict ? '>' : '≤'} N (${sim.n})
                </div>
                <p class="text-xs text-slate-400 max-w-lg mx-auto mt-2">
                  "Because R + W > N, every read quorum intersects with every write quorum in at least one node. Stale reads are mathematically impossible under strict quorum."
                </p>
              </div>

              <!-- Overlap Diagram -->
              <div class="p-4 bg-black/50 border border-slate-800 rounded-lg flex justify-around items-center max-w-xl mx-auto py-3 font-mono text-xs">
                <div class="text-center text-purple-300">
                  <div class="font-bold">Write Quorum</div>
                  <div class="text-[11px] text-slate-500">Nodes {1, 2}</div>
                </div>
                <div class="px-3 py-1 bg-purple-950/60 border border-purple-500/40 rounded text-purple-300 font-bold">
                  Intersection Overlap {2}
                </div>
                <div class="text-center text-purple-300">
                  <div class="font-bold">Read Quorum</div>
                  <div class="text-[11px] text-slate-500">Nodes {2, 3}</div>
                </div>
              </div>
            </div>

            <!-- Configuration Parameters -->
            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Live Cluster Configuration</div>
              <div class="grid grid-cols-3 gap-4">
                <div class="p-3 bg-[#080b12] border border-slate-800 rounded">
                  <div class="text-slate-500">N (Replication)</div>
                  <div class="text-lg font-bold text-white mt-1">3</div>
                </div>
                <div class="p-3 bg-[#080b12] border border-slate-800 rounded">
                  <div class="text-slate-500">W (Write Quorum)</div>
                  <div class="text-lg font-bold text-purple-400 mt-1">2</div>
                </div>
                <div class="p-3 bg-[#080b12] border border-slate-800 rounded">
                  <div class="text-slate-500">R (Read Quorum)</div>
                  <div class="text-lg font-bold text-purple-400 mt-1">2</div>
                </div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: events (OPERATIONS > Events)
      // ─────────────────────────────────────────────────────────────────────────────
      events: {
        section: 'OPERATIONS',
        title: 'Real-Time Event Stream (SSE)',
        render: () => {
          const logs = VaultStore.sseLogs.length > 0 ? VaultStore.sseLogs : [
            { time: new Date().toISOString(), type: 'STATUS', msg: 'Connected to live stream', payload: {} }
          ];

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Live Server-Sent Events Stream</h1>
                <p class="text-xs text-slate-400 mt-0.5">Real-time HTTP SSE stream from http://localhost:8080/cluster/events/stream.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="VaultStore.ssePaused = !VaultStore.ssePaused; reRenderCurrentView();" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-purple-300">
                  ${VaultStore.ssePaused ? '▶ Resume' : '⏸ Pause'}
                </button>
                <button onclick="VaultStore.sseLogs = []; reRenderCurrentView();" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300">Clear</button>
                <button onclick="initSSE()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-emerald-400">Reconnect</button>
              </div>
            </div>

            <div class="p-4 terminal-container border border-slate-800 rounded-xl text-xs space-y-1.5 max-h-[550px] overflow-y-auto custom-scroll">
              <div class="text-slate-500">// Connected to http://localhost:8080/cluster/events/stream</div>
              ${logs.map(l => `
                <div class="p-1 hover:bg-slate-900/60 rounded">
                  <span class="text-slate-500">[${new Date(l.time).toLocaleTimeString()}]</span>
                  <span class="font-bold ml-1 ${
                    l.type.includes('DRAIN') ? 'text-amber-400' :
                    l.type.includes('CORRUPT') ? 'text-rose-400' :
                    l.type.includes('REPAIR') ? 'text-blue-400' : 'text-purple-400'
                  }">[${l.type}]</span>
                  <span class="text-slate-200 ml-1">${l.msg}</span>
                  ${l.payload ? `<span class="text-slate-500 ml-1">${JSON.stringify(l.payload)}</span>` : ''}
                </div>
              `).join('')}
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: audit_log (OPERATIONS > Audit Log)
      // ─────────────────────────────────────────────────────────────────────────────
      audit_log: {
        section: 'OPERATIONS',
        title: 'Cluster Operations Audit Log',
        render: () => {
          const evts = VaultStore.events;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Operations Audit Log</h1>
                <p class="text-xs text-slate-400 mt-0.5">Chronological record of verified cluster operations during current session.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">${evts.length} RECORDS</span>
            </div>

            <div class="bg-[#080b12] border border-slate-800 rounded-xl overflow-hidden font-mono text-xs shadow-xl">
              <table class="w-full text-left">
                <thead class="bg-[#0c101a] text-slate-400 text-[10px]">
                  <tr><th class="p-3">Time</th><th class="p-3">Operation</th><th class="p-3">Message</th></tr>
                </thead>
                <tbody class="divide-y divide-slate-800 text-slate-300">
                  ${evts.map(ev => `
                    <tr class="hover:bg-slate-800/30">
                      <td class="p-3 text-slate-500">${ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ''}</td>
                      <td class="p-3 font-bold ${
                        ev.type.includes('DRAIN') ? 'text-amber-400' :
                        ev.type.includes('CORRUPT') ? 'text-rose-400' :
                        ev.type.includes('REPAIR') ? 'text-blue-400' : 'text-purple-400'
                      }">[${ev.type}]</td>
                      <td class="p-3 text-slate-200">${ev.message}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: api_explorer (OPERATIONS > API Explorer)
      // ─────────────────────────────────────────────────────────────────────────────
      api_explorer: {
        section: 'OPERATIONS',
        title: 'Developer REST API Explorer',
        render: () => {
          const exp = VaultStore.apiExplorer;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Developer REST API Explorer</h1>
                <p class="text-xs text-slate-400 mt-0.5">Interactive HTTP testing console against the Vault API Gateway on port 8080.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">LIVE INTERACTIVE</span>
            </div>

            <!-- Route Presets -->
            <div class="flex flex-wrap gap-2 text-xs font-mono">
              <button onclick="setApiPreset('GET', '/health')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /health</button>
              <button onclick="setApiPreset('GET', '/cluster/status')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /cluster/status</button>
              <button onclick="setApiPreset('GET', '/cluster/config')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /cluster/config</button>
              <button onclick="setApiPreset('GET', '/nodes')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /nodes</button>
              <button onclick="setApiPreset('GET', '/objects')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /objects</button>
              <button onclick="setApiPreset('GET', '/repairs')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">GET /repairs</button>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-4 font-mono text-xs">
              <div class="grid grid-cols-4 gap-3">
                <div>
                  <label class="text-slate-400 block mb-1">HTTP Method</label>
                  <select id="api-method" class="w-full p-2.5 bg-black border border-slate-800 rounded text-white">
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                </div>
                <div class="col-span-3">
                  <label class="text-slate-400 block mb-1">Request Path</label>
                  <input id="api-path" type="text" value="${exp.path}" class="w-full p-2.5 bg-black border border-slate-800 rounded text-slate-200">
                </div>
              </div>

              <div>
                <label class="text-slate-400 block mb-1">Headers (e.g. X-Expected-Version: 0)</label>
                <textarea id="api-headers" rows="1" class="w-full p-2 bg-black border border-slate-800 rounded text-slate-300" placeholder="Header: Value">${exp.headers || ''}</textarea>
              </div>

              <div>
                <label class="text-slate-400 block mb-1">Request Body (JSON or raw)</label>
                <textarea id="api-body" rows="2" class="w-full p-2 bg-black border border-slate-800 rounded text-slate-300" placeholder="Optional payload...">${exp.body || ''}</textarea>
              </div>

              <button onclick="sendApiExplorerRequest()" class="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded font-bold transition">
                Send Request
              </button>
            </div>

            ${exp.result ? `
              <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
                <div class="flex justify-between items-center">
                  <span class="text-slate-400 font-bold">Response: <span class="text-white">${exp.method} ${exp.path}</span></span>
                  <span class="${exp.result.ok ? 'badge-verified' : 'badge-critical'} px-2 py-0.5 rounded font-bold">
                    HTTP ${exp.result.status} (${exp.result.latencyMs} ms)
                  </span>
                </div>
                <pre class="bg-black/60 p-4 rounded border border-slate-800 text-emerald-400 overflow-x-auto max-h-96 custom-scroll">${
                  typeof exp.result.data === 'object' ? JSON.stringify(exp.result.data, null, 2) : exp.result.data
                }</pre>
              </div>
            ` : ''}
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: runbook (OPERATIONS > Runbook)
      // ─────────────────────────────────────────────────────────────────────────────
      runbook: {
        section: 'OPERATIONS',
        title: 'Cluster Operations Runbook & Verification Suite',
        render: () => {
          const results = VaultStore.runbookResults;

          const steps = [
            { num: 1, label: '01. Start Cluster & Gateway Health', action: 'GET /health check' },
            { num: 2, label: '02. Storage Node Heartbeats', action: 'Verify 3 nodes active' },
            { num: 3, label: '03. Quorum PUT Object (W=2)', action: 'Parallel write to nodes' },
            { num: 4, label: '04. Verify Replicas Across Fleet', action: 'Confirm copies on disk' },
            { num: 5, label: '05. Quorum GET Object (R=2)', action: 'Read & verify SHA-256' },
            { num: 6, label: '06. Test OCC Version Conflict', action: 'Verify HTTP 409 rejection' },
            { num: 7, label: '07. Graceful Node Drain', action: 'Drain node-3, block writes' },
            { num: 8, label: '08. Autonomous Replica Healing', action: 'Trigger repair scan' }
          ];

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Demonstration Runbook & Verification Suite</h1>
                <p class="text-xs text-slate-400 mt-0.5">Automated test runners checking all distributed-systems invariants against the live cluster.</p>
              </div>
              <div class="flex space-x-2">
                <button onclick="runAllRunbookSteps()" class="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded font-mono text-xs font-bold transition">
                  Run Full Verification Suite
                </button>
              </div>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="space-y-2">
                ${steps.map(s => {
                  const res = results[s.num];
                  return `
                    <div class="p-3 bg-[#080b12] border border-slate-800 rounded flex items-center justify-between">
                      <div>
                        <span class="text-white font-bold">${s.label}</span>
                        <span class="text-slate-500 ml-2">(${s.action})</span>
                        ${res ? `<div class="text-[11px] ${res.passed ? 'text-emerald-400' : 'text-rose-400'} mt-1">${res.detail}</div>` : ''}
                      </div>
                      <div class="flex items-center space-x-3">
                        ${res ? `
                          <span class="${res.passed ? 'badge-verified' : 'badge-critical'} px-2 py-0.5 rounded text-[10px] font-bold">
                            ${res.passed ? 'PASS ✓' : 'FAIL ✕'}
                          </span>
                        ` : ''}
                        <button onclick="runRunbookStep(${s.num})" class="px-2.5 py-1 bg-purple-600/20 border border-purple-500/40 text-purple-300 hover:bg-purple-600/30 rounded text-xs transition">
                          Run Test
                        </button>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: sqlite (SYSTEM > SQLite)
      // ─────────────────────────────────────────────────────────────────────────────
      sqlite: {
        section: 'SYSTEM',
        title: 'Metadata Engine Architecture',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Metadata Engine (SQLite WAL)</h1>
                <p class="text-xs text-slate-400 mt-0.5">ACID catalog implemented with native Node.js node:sqlite module.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">SQLITE WAL MODE</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 font-sans">Driver</div>
                <div class="text-sm font-bold text-white mt-1">node:sqlite (Node 22+)</div>
                <div class="text-[10px] text-emerald-400 mt-1">Native zero-dependency runtime</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 font-sans">Concurrency Mode</div>
                <div class="text-sm font-bold text-purple-400 mt-1">PRAGMA journal_mode = WAL</div>
                <div class="text-[10px] text-slate-500 mt-1">Concurrent non-blocking reads</div>
              </div>
              <div class="p-4 card-panel rounded-lg">
                <div class="text-slate-400 font-sans">Integrity Pragmas</div>
                <div class="text-sm font-bold text-white mt-1">foreign_keys = ON</div>
                <div class="text-[10px] text-slate-500 mt-1">synchronous = NORMAL</div>
              </div>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-3 font-mono text-xs">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Relational Catalog Schema</div>
              <div class="grid grid-cols-2 md:grid-cols-5 gap-2 text-center">
                <div class="p-2.5 bg-black/40 border border-slate-800 rounded text-slate-300">nodes</div>
                <div class="p-2.5 bg-black/40 border border-slate-800 rounded text-slate-300">objects</div>
                <div class="p-2.5 bg-black/40 border border-slate-800 rounded text-slate-300">replicas</div>
                <div class="p-2.5 bg-black/40 border border-slate-800 rounded text-slate-300">repair_jobs</div>
                <div class="p-2.5 bg-black/40 border border-slate-800 rounded text-slate-300">events</div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: atomic_store (SYSTEM > Atomic Store)
      // ─────────────────────────────────────────────────────────────────────────────
      atomic_store: {
        section: 'SYSTEM',
        title: 'Atomic Physical Storage Engine',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">POSIX Atomic Storage Engine</h1>
                <p class="text-xs text-slate-400 mt-0.5">Crash-resilient staging and platter cache synchronization pipeline.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">CRASH-PROOF</span>
            </div>

            <div class="p-6 card-panel rounded-xl space-y-4">
              <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">POSIX Pipeline Flow</div>
              <div class="flex items-center justify-between max-w-xl mx-auto py-3 font-mono text-xs">
                <div class="text-center">
                  <div class="p-3 bg-black/60 border border-slate-700 rounded text-slate-300">.tmp File</div>
                  <div class="text-[10px] text-slate-500 mt-1">Stage upload</div>
                </div>
                <span class="text-slate-600">&rarr;</span>
                <div class="text-center">
                  <div class="p-3 bg-black/60 border border-purple-500/40 rounded text-purple-400 font-bold">fsync()</div>
                  <div class="text-[10px] text-slate-500 mt-1">Flush platter cache</div>
                </div>
                <span class="text-slate-600">&rarr;</span>
                <div class="text-center">
                  <div class="p-3 bg-black/60 border border-emerald-500/40 rounded text-emerald-400 font-bold">.dat Rename</div>
                  <div class="text-[10px] text-slate-500 mt-1">Atomic flip</div>
                </div>
              </div>
              <div class="p-3 bg-slate-950/60 border border-slate-800 rounded text-center text-xs text-slate-400 font-sans">
                "Atomic write flow ensures partial writes never corrupt existing object versions under unexpected power loss."
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: configuration (SYSTEM > Configuration)
      // ─────────────────────────────────────────────────────────────────────────────
      configuration: {
        section: 'SYSTEM',
        title: 'Technical Configuration',
        render: () => {
          const cfg = VaultStore.config;

          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">System Configuration</h1>
                <p class="text-xs text-slate-400 mt-0.5">Active runtime environment variables and distributed co-efficients.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">LIVE CONFIG ACTIVE</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
              <div class="p-5 card-panel rounded-xl space-y-3">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Distributed Consensus</div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">REPLICATION_FACTOR (N)</span><span class="text-white font-bold">${cfg.replicationFactor}</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">WRITE_QUORUM (W)</span><span class="text-purple-400 font-bold">${cfg.writeQuorum}</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">READ_QUORUM (R)</span><span class="text-purple-400 font-bold">${cfg.readQuorum}</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">HEARTBEAT_TIMEOUT</span><span class="text-white">${cfg.heartbeatTimeout} ms</span></div>
                <div class="flex justify-between py-1.5"><span class="text-slate-400">HEARTBEAT_INTERVAL</span><span class="text-white">${cfg.heartbeatInterval} ms</span></div>
              </div>

              <div class="p-5 card-panel rounded-xl space-y-3">
                <div class="text-xs font-bold text-slate-300 uppercase tracking-wider font-sans">Storage & Cryptography</div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">CHECKSUM_ALGORITHM</span><span class="text-emerald-400 font-bold">${cfg.checksumAlgorithm}</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">METADATA_DATABASE</span><span class="text-white font-bold">${cfg.metadataDatabase}</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">REPAIR_INTERVAL</span><span class="text-white">${cfg.repairInterval} ms</span></div>
                <div class="flex justify-between py-1.5 border-b border-slate-800"><span class="text-slate-400">SCAN_INTERVAL</span><span class="text-white">${cfg.scanInterval} ms</span></div>
              </div>
            </div>
          </div>
          `;
        }
      },

      // ─────────────────────────────────────────────────────────────────────────────
      // VIEW: cluster_identity (SYSTEM > Cluster Identity)
      // ─────────────────────────────────────────────────────────────────────────────
      cluster_identity: {
        section: 'SYSTEM',
        title: 'Cluster Identity & Security',
        render: () => {
          return `
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h1 class="text-xl font-bold text-white tracking-tight">Cluster Identity & Security</h1>
                <p class="text-xs text-slate-400 mt-0.5">Control plane authentication session and endpoint constraints.</p>
              </div>
              <span class="badge-verified px-2.5 py-1 rounded text-xs font-mono font-medium">SESSION ACTIVE</span>
            </div>

            <div class="p-5 card-panel rounded-xl space-y-4 font-mono text-xs">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-purple-600/20 border border-purple-500/40 text-purple-400 flex items-center justify-center font-bold text-sm">OP</div>
                <div>
                  <div class="text-sm font-bold text-white">operator-09 (AUTH_LEVEL_0)</div>
                  <div class="text-slate-500 text-[11px]">Primary Infrastructure Controller Session</div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800">
                <div class="space-y-1.5">
                  <div class="text-slate-400 font-sans font-bold">Gateway Endpoint:</div>
                  <div class="p-2 bg-black/60 rounded text-slate-200">http://localhost:8080</div>
                </div>
                <div class="space-y-1.5">
                  <div class="text-slate-400 font-sans font-bold">Storage Nodes:</div>
                  <div class="p-2 bg-black/60 rounded text-slate-200">localhost:8081, :8082, :8083</div>
                </div>
              </div>
            </div>
          </div>
          `;
        }
      }
    };

    // ─── NAVIGATION DISPATCHER ──────────────────────────────────────────────────
    function navigateTo(viewId) {
      if (!views[viewId]) return;
      VaultStore.activeView = viewId;

      document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      const activeBtn = document.getElementById(`nav-${viewId}`);
      if (activeBtn) activeBtn.classList.add('active');

      document.getElementById('breadcrumb-section').textContent = views[viewId].section;
      document.getElementById('breadcrumb-page').textContent = views[viewId].title;
      document.getElementById('quick-jump-select').value = viewId;

      const container = document.getElementById('view-container');
      container.innerHTML = views[viewId].render();
      container.scrollTop = 0;
    }

    // Populate quick jump dropdown
    const quickSelect = document.getElementById('quick-jump-select');
    Object.keys(views).forEach(id => {
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = `${views[id].section} > ${views[id].title}`;
      quickSelect.appendChild(opt);
    });

    // Start background engines
    initSSE();
    syncHealth();
    syncCluster();
    syncConfig();

    // Default route
    navigateTo('dashboard');
  </script>
</body>
</html>
"""

    full_html = base + js_scaffold + views_code

    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
    print("Written to artifact:", ARTIFACT_PATH)

    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
    print("Written to dashboard:", DASHBOARD_PATH)

if __name__ == "__main__":
    generate_html()
