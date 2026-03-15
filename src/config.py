import os
from pathlib import Path

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "auto")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-2.5-flash")

# Eval — DeepEval self-healing
MAX_EVAL_RETRIES = int(os.getenv("MAX_EVAL_RETRIES", "2"))
EVAL_THRESHOLD = float(os.getenv("EVAL_THRESHOLD", "0.6"))

# Context cache
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "1800"))

# Steam
STEAM_APP_ID = int(os.getenv("STEAM_APP_ID", "1363080"))
WORKSHOP_GUIDE_IDS = [
    gid.strip()
    for gid in os.getenv("WORKSHOP_GUIDE_IDS", "3427105626").split(",")
    if gid.strip()
]

# Paths — inside Docker, saves are always mounted at /saves
SAVE_FOLDER = Path(os.getenv("WATCH_PATH", "/saves"))
CONFIGS_DIR = Path(__file__).parent.parent / "configs"
GUIDES_DIR = Path(__file__).parent.parent / "guides"
DATA_DIR = Path(__file__).parent.parent / "data"

# Dashboard
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

# Session
SESSION_MAX_ENTRIES = int(os.getenv("SESSION_MAX_ENTRIES", "10"))

# Watcher
DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "2.0"))
