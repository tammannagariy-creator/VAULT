#!/usr/bin/env python3
"""
scripts/build_full_application.py
Assembles and compiles the full Hackathon Production Control Plane.
"""

import os
import sys

ARTIFACT_PATH = r"C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html"
DASHBOARD_PATH = r"C:\surya\vault\dashboard\public\index.html"

# Import components
import build_hackathon_control_plane
import app_js
import app_views_hackathon
import app_views_core

def assemble():
    head = build_hackathon_control_plane.get_html_head()
    js_runtime = app_js.get_js_runtime()
    hackathon_views = app_views_hackathon.get_hackathon_views()
    core_views = app_views_core.get_core_views()

    views_wrapper = (
        "\n    // ═══════════════════════════════════════════════════════════════════════════\n"
        "    // 28 PRODUCTION VIEWS FOR HACKATHON CONTROL ROOM\n"
        "    // ═══════════════════════════════════════════════════════════════════════════\n"
        "    window.views = {\n"
        + hackathon_views
        + "\n"
        + core_views
        + """
    };

    // ─── INITIALIZATION ON LOAD ──────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
      // Populate quick-jump selector
      const quickSelect = document.getElementById('quick-jump-select');
      if (quickSelect) {
        quickSelect.innerHTML = '<option value="" disabled selected>Jump to View...</option>';
        Object.keys(window.views).forEach(id => {
          const opt = document.createElement('option');
          opt.value = id;
          opt.textContent = `${window.views[id].section} > ${window.views[id].title}`;
          quickSelect.appendChild(opt);
        });
      }

      // Start background telemetry engines
      initSSE();
      syncHealth();
      syncCluster();
      syncConfig();

      // Launch default route (Hackathon Overview)
      navigateTo('presentation');
    });
  </script>
</body>
</html>
"""
    )

    full_html = head + js_runtime + views_wrapper

    print(f"Total HTML Document Length: {len(full_html)} characters")

    # Write to artifact
    with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Successfully wrote artifact: {ARTIFACT_PATH}")

    # Write to dashboard
    os.makedirs(os.path.dirname(DASHBOARD_PATH), exist_ok=True)
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Successfully wrote dashboard index: {DASHBOARD_PATH}")

if __name__ == '__main__':
    assemble()
