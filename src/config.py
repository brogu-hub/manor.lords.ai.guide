import os
from pathlib import Path

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Set PRIMARY_MODEL="auto" (default) to auto-detect the latest flash model
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "auto")
FALLBACK_MODEL = "gemini-2.5-flash"

# Paths — inside Docker, saves are always mounted at /saves
SAVE_FOLDER = Path(os.getenv("WATCH_PATH", "/saves"))
CONFIGS_DIR = Path(__file__).parent.parent / "configs"
GUIDES_DIR = Path(__file__).parent.parent / "guides"
DATA_DIR = Path(__file__).parent.parent / "data"

# Dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

# Watcher
DEBOUNCE_SECONDS = 2.0
