"""SQLite-based request/response logger for Gemini API calls."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "request_log.db"

_conn: sqlite3.Connection | None = None


def init_db():
    """Create the requests table if it doesn't exist."""
    global _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            model           TEXT    NOT NULL,
            request_type    TEXT    NOT NULL,
            system_prompt   TEXT,
            user_prompt     TEXT,
            thinking_budget INTEGER,
            temperature     REAL,
            max_tokens      INTEGER,
            response_text   TEXT,
            response_chars  INTEGER,
            duration_ms     INTEGER,
            error           TEXT,
            game_year       INTEGER,
            game_season     TEXT,
            alerts          TEXT
        )
    """)
    _conn.commit()
    logger.info("Request log DB initialised at %s", DB_PATH)


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        init_db()
    return _conn


def log_request(
    *,
    model: str,
    request_type: str,
    system_prompt: str = "",
    user_prompt: str = "",
    thinking_budget: int | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_text: str | None = None,
    duration_ms: int | None = None,
    error: str | None = None,
    game_year: int | None = None,
    game_season: str | None = None,
    alerts: list[str] | None = None,
):
    """Insert a request/response log entry."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO requests (
            timestamp, model, request_type, system_prompt, user_prompt,
            thinking_budget, temperature, max_tokens,
            response_text, response_chars, duration_ms, error,
            game_year, game_season, alerts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            model,
            request_type,
            system_prompt,
            user_prompt,
            thinking_budget,
            temperature,
            max_tokens,
            response_text,
            len(response_text) if response_text else None,
            duration_ms,
            error,
            game_year,
            game_season,
            json.dumps(alerts) if alerts else None,
        ),
    )
    conn.commit()


def get_recent_logs(limit: int = 50) -> list[dict]:
    """Return the most recent log entries."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM requests ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.row_factory = None
    return [dict(row) for row in rows]
