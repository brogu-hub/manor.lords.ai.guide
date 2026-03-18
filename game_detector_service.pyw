"""Background game detector — runs on Windows host at login.

Watches Steam registry for Manor Lords launch, auto-opens the dashboard.
Uses zero CPU (kernel-level registry notification, no polling).
.pyw extension = no console window.
"""

import sys
import time
import logging

logging.basicConfig(
    filename=sys.path[0] + "/game_detector.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

# Add project root to path
sys.path.insert(0, sys.path[0])

from src.watcher.game_detector import start_game_detector

DASHBOARD_URL = "http://localhost:7860"

logging.info("Game detector started — watching for Manor Lords launch")
start_game_detector(DASHBOARD_URL)

# Keep alive (detector runs in a daemon thread)
while True:
    time.sleep(3600)
