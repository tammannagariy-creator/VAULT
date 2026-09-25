#!/usr/bin/env python3
r"""
Vault Distributed Object Storage — Hackathon Production Control Plane Builder
Generates the complete, high-fidelity single-page application with real-time backend integration.
Outputs to:
  - C:\surya\vault\dashboard\public\index.html (Gateway hosted at http://localhost:8080/ui/)
  - C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html
"""

import os
import sys

ARTIFACT_PATH = r"C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html"
DASHBOARD_PATH = r"C:\surya\vault\dashboard\public\index.html"

def get_html_head():
    return """<!DOCTYPE html>
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
    .badge-simulation { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .card-panel { background: #0a0d16; border: 1px solid #161c2d; }
    .card-panel:hover { border-color: #242d45; }
    .nav-btn { transition: all 0.15s ease; }
    .nav-btn:hover { background: rgba(30, 41, 59, 0.6); color: #ffffff; }
    .nav-btn.active { background: #151b2c; color: #ffffff; border-left: 2px solid #8b5cf6; font-weight: 600; }
    .terminal-container { background: #040508; font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="h-screen overflow-hidden flex flex-col bg-[#06080d] text-slate-300 select-none">

  <!-- TOAST CONTAINER -->
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
        <span id="breadcrumb-section">PRESENTATION</span>
        <span class="text-slate-700">&rsaquo;</span>
        <span id="breadcrumb-page" class="text-slate-200 font-semibold">Hackathon Overview</span>
      </div>
    </div>

    <!-- Live Cluster Real-Time Telemetry Badges -->
    <div class="flex items-center space-x-2.5 text-xs">
      <!-- Gateway Connection Badge -->
      <div id="header-conn-badge" class="flex items-center space-x-2 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1">
        <span id="header-conn-dot" class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span id="header-conn-text" class="text-emerald-300 font-mono font-medium">● GATEWAY CONNECTED</span>
        <span class="text-slate-600">|</span>
        <span class="text-slate-400 text-[11px]">LAST UPDATE:</span>
        <span id="header-sync-time" class="text-slate-200 font-mono text-[11px]">--:--:--</span>
      </div>

      <!-- SSE Pill -->
      <div class="flex items-center space-x-1.5 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 font-mono text-xs">
        <span id="header-sse-dot" class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span id="header-sse-status" class="text-emerald-400 font-semibold">● SSE CONNECTED</span>
      </div>

      <!-- Cluster Health Pill -->
      <div class="flex items-center space-x-1.5 bg-[#0a0d16] border border-slate-800 rounded px-2.5 py-1 font-mono text-xs">
        <span class="text-slate-400">Cluster:</span>
        <span id="header-cluster-status" class="text-amber-400 font-semibold">DEGRADED</span>
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
    <aside class="w-64 border-r border-slate-800/80 bg-[#070910] flex flex-col justify-between shrink-0 select-none">
      <div class="p-3 overflow-y-auto custom-scroll flex-1 space-y-4">
        
        <!-- SECTION: HACKATHON DEMO -->
        <div>
          <div class="text-[10px] font-bold text-purple-400 uppercase tracking-widest px-2 mb-1 flex items-center justify-between">
            <span>HACKATHON DEMO</span>
            <span class="text-[9px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded">JUDGES</span>
          </div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('presentation')" id="nav-presentation" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span class="font-medium text-white">1. Hackathon Overview</span>
              <span class="text-[10px] font-mono text-purple-400 font-bold">PITCH</span>
            </button>
            <button onclick="navigateTo('demo_mode')" id="nav-demo_mode" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span class="font-medium text-white">2. Guided 8-Step Demo</span>
              <span class="text-[10px] font-mono text-emerald-400 font-bold">LIVE</span>
            </button>
          </div>
        </div>

        <!-- SECTION: CLUSTER CONTROL -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">CLUSTER CONTROL</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('dashboard')" id="nav-dashboard" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Dashboard</span>
              <span class="text-[10px] font-mono text-emerald-400">LIVE</span>
            </button>
            <button onclick="navigateTo('nodes')" id="nav-nodes" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Node Monitor</span>
              <span id="nav-badge-nodes" class="text-[10px] font-mono text-slate-500">3 Hosts</span>
            </button>
            <button onclick="navigateTo('node_detail')" id="nav-node_detail" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Node Detail</span>
              <span id="nav-badge-selected-node" class="text-[10px] font-mono text-amber-400">node-3</span>
            </button>
            <button onclick="navigateTo('topology')" id="nav-topology" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Topology</span>
              <span class="text-[10px] font-mono text-slate-500">N=3</span>
            </button>
            <button onclick="navigateTo('membership')" id="nav-membership" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Membership & Heartbeats</span>
              <span class="text-[10px] font-mono text-emerald-400">5s cycle</span>
            </button>
            <button onclick="navigateTo('gateway')" id="nav-gateway" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Gateway Health</span>
              <span class="text-[10px] font-mono text-slate-500">:8080</span>
            </button>
          </div>
        </div>

        <!-- SECTION: STORAGE -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">OBJECT STORAGE</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('objects')" id="nav-objects" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Object Browser</span>
              <span id="nav-badge-obj-count" class="text-[10px] font-mono text-slate-500">0 objs</span>
            </button>
            <button onclick="navigateTo('object_detail')" id="nav-object_detail" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Object Detail</span>
              <span class="text-[10px] font-mono text-slate-500">Inspect</span>
            </button>
            <button onclick="navigateTo('upload')" id="nav-upload" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span class="text-white font-medium">Live Object Upload</span>
              <span class="text-[10px] font-mono text-emerald-400 font-bold">PUT</span>
            </button>
            <button onclick="navigateTo('versions')" id="nav-versions" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Version & OCC Conflict</span>
              <span class="text-[10px] font-mono text-purple-400">409 Test</span>
            </button>
            <button onclick="navigateTo('integrity')" id="nav-integrity" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Integrity & Checksums</span>
              <span class="text-[10px] font-mono text-emerald-400">SHA-256</span>
            </button>
            <button onclick="navigateTo('replicas')" id="nav-replicas" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Replica Distribution</span>
              <span class="text-[10px] font-mono text-emerald-400">Disk paths</span>
            </button>
            <button onclick="navigateTo('buckets')" id="nav-buckets" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Buckets & Namespaces</span>
              <span class="text-[10px] font-mono text-slate-500">Virtual</span>
            </button>
          </div>
        </div>

        <!-- SECTION: RELIABILITY -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">RELIABILITY & QUORUM</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('quorum')" id="nav-quorum" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Quorum Calculator</span>
              <span class="text-[10px] font-mono text-purple-400">R+W &gt; N</span>
            </button>
            <button onclick="navigateTo('drain_node')" id="nav-drain_node" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Node Drain Panel</span>
              <span class="text-[10px] font-mono text-amber-400">Decommission</span>
            </button>
            <button onclick="navigateTo('fault_injection')" id="nav-fault_injection" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Fault Injection Lab</span>
              <span class="text-[10px] font-mono text-rose-400 font-bold">HAZARD</span>
            </button>
            <button onclick="navigateTo('repairs')" id="nav-repairs" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Replica Repair Center</span>
              <span id="nav-badge-repairs" class="text-[10px] font-mono text-slate-500">0 jobs</span>
            </button>
            <button onclick="navigateTo('rebalancing')" id="nav-rebalancing" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Rebalancer</span>
              <span class="text-[10px] font-mono text-slate-500">Daemon</span>
            </button>
          </div>
        </div>

        <!-- SECTION: OPERATIONS -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">OPERATIONS & AUDIT</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('events')" id="nav-events" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Live Event Stream</span>
              <span class="text-[10px] font-mono text-emerald-400">SSE</span>
            </button>
            <button onclick="navigateTo('audit_log')" id="nav-audit_log" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Operations Audit Log</span>
              <span class="text-[10px] font-mono text-slate-500">History</span>
            </button>
            <button onclick="navigateTo('api_explorer')" id="nav-api_explorer" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Developer API Explorer</span>
              <span class="text-[10px] font-mono text-purple-400">REST</span>
            </button>
            <button onclick="navigateTo('runbook')" id="nav-runbook" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Demonstration Runbook</span>
              <span class="text-[10px] font-mono text-slate-500">Docs</span>
            </button>
          </div>
        </div>

        <!-- SECTION: SYSTEM -->
        <div>
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-1">SYSTEM ARCHITECTURE</div>
          <div class="space-y-0.5">
            <button onclick="navigateTo('sqlite')" id="nav-sqlite" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>SQLite WAL Engine</span>
              <span class="text-[10px] font-mono text-slate-500">Driver</span>
            </button>
            <button onclick="navigateTo('atomic_store')" id="nav-atomic_store" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Atomic Physical Storage</span>
              <span class="text-[10px] font-mono text-slate-500">POSIX</span>
            </button>
            <button onclick="navigateTo('configuration')" id="nav-configuration" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Configuration</span>
              <span class="text-[10px] font-mono text-slate-500">JSON</span>
            </button>
            <button onclick="navigateTo('cluster_identity')" id="nav-cluster_identity" class="nav-btn w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-left text-slate-400">
              <span>Cluster Identity</span>
              <span class="text-[10px] font-mono text-slate-500">Security</span>
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
      <!-- Views are dynamically rendered here -->
    </main>

  </div>
"""

print("HTML head defined.")
