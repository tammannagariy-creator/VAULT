"""
scripts/build_app.py
Generates the complete Hackathon Production Control Plane.
"""

import os
import sys

ARTIFACT_PATH = r"C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html"
DASHBOARD_PATH = r"C:\surya\vault\dashboard\public\index.html"

# We read the shell from build_hackathon_control_plane.py
import build_hackathon_control_plane

head = build_hackathon_control_plane.get_html_head()

print("Head retrieved, length:", len(head))
