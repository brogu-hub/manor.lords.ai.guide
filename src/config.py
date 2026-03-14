import os
from pathlib import Path

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini-2.5-flash")

FALLBACK_CHAIN = [
    PRIMARY_MODEL,
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
]

# Paths — inside Docker, saves are always mounted at /saves
SAVE_FOLDER = Path(os.getenv("WATCH_PATH", "/saves"))
CONFIGS_DIR = Path(__file__).parent.parent / "configs"
GUIDES_DIR = Path(__file__).parent.parent / "guides"
DATA_DIR = Path(__file__).parent.parent / "data"

# Dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

# Watcher
DEBOUNCE_SECONDS = 2.0
