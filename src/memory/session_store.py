"""Simple JSON-based session store for MVP (replaces Graphiti)."""

import json
import logging
from datetime import datetime

from src.config import DATA_DIR, SESSION_MAX_ENTRIES

logger = logging.getLogger(__name__)

STORE_PATH = DATA_DIR / "session_history.json"


def _ensure_store():
    """Create the data directory and store file if they don't exist."""
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text("[]", encoding="utf-8")


def load_history() -> list[dict]:
    """Load session history from JSON file."""
    _ensure_store()
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_entry(state_summary: dict, advice_summary: str):
    """Append a new entry to session history."""
    _ensure_store()
    history = load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "state": state_summary,
        "advice": advice_summary,
    }

    history.append(entry)

    # Keep only last N entries
    if len(history) > SESSION_MAX_ENTRIES:
        history = history[-SESSION_MAX_ENTRIES:]

    STORE_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Session entry saved (%d total)", len(history))


def get_session_context(last_n: int = 3) -> str:
    """Build a text context string from the last N session entries.

    This is injected into the LLM prompt for continuity.
    """
    history = load_history()
    if not history:
        return ""

    recent = history[-last_n:]
    lines = ["PREVIOUS SAVES THIS SESSION:"]
    for entry in recent:
        ts = entry.get("timestamp", "unknown")
        state = entry.get("state", {})
        advice = entry.get("advice", "")
        lines.append(f"\n[{ts}]")
        if state:
            lines.append(f"  State: Year {state.get('year', '?')}, "
                         f"Season {state.get('season', '?')}, "
                         f"Food {state.get('food', '?')}, "
                         f"Approval {state.get('approval', '?')}")
        if advice:
            lines.append(f"  Advice given: {advice[:200]}")

    return "\n".join(lines)
