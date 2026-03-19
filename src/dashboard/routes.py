"""Dashboard API routes — REST + SSE endpoints."""

import asyncio
import json
import logging
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.strategy.response_parser import AdviceResponse
from src.config import DATA_DIR, HISTORY_MAX_ENTRIES

logger = logging.getLogger(__name__)

router = APIRouter()

# --- SQLite persistence ---
_DB_PATH = DATA_DIR / "dashboard.db"
_db: sqlite3.Connection | None = None


def _get_db() -> sqlite3.Connection:
    global _db
    if _db is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        _db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT NOT NULL,
                save_name  TEXT,
                summary    TEXT,
                priority_1 TEXT,
                state_json TEXT,
                advice_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # Migrate: add columns if upgrading from old schema
        for col, col_type in [
            ("save_name", "TEXT"),
            ("state_json", "TEXT"),
            ("advice_json", "TEXT"),
            ("trajectory_label", "TEXT"),
            ("trajectory_score", "REAL"),
            ("trajectory_reasoning", "TEXT"),
            ("trajectory_strengths", "TEXT"),
            ("trajectory_risks", "TEXT"),
            ("embedding", "TEXT"),
        ]:
            try:
                _db.execute(f"ALTER TABLE history ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        _db.commit()
        logger.info("Dashboard DB initialised at %s", _DB_PATH)
    return _db


def _db_set(key: str, value: str):
    db = _get_db()
    db.execute(
        "INSERT OR REPLACE INTO cache (key, value, updated_at) VALUES (?, ?, datetime('now'))",
        (key, value),
    )
    db.commit()


def _db_get(key: str) -> str | None:
    db = _get_db()
    row = db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


# In-memory state shared with the pipeline
_current_state: dict | None = None
_current_advice: AdviceResponse | None = None
_history: list[dict] = []
_sse_subscribers: list[asyncio.Queue] = []


def _load_cached():
    """Load persisted state/advice from database on startup."""
    global _current_state, _current_advice, _history
    try:
        raw = _db_get("state")
        if raw:
            _current_state = json.loads(raw)
            logger.info("Loaded cached game state from DB")
    except Exception as e:
        logger.warning("Failed to load cached state: %s", e)
    try:
        raw = _db_get("advice")
        if raw:
            _current_advice = AdviceResponse(**json.loads(raw))
            logger.info("Loaded cached advice from DB")
    except Exception as e:
        logger.warning("Failed to load cached advice: %s", e)
    try:
        db = _get_db()
        rows = db.execute(
            "SELECT id, timestamp, save_name, summary, priority_1 FROM history ORDER BY id DESC LIMIT ?",
            (HISTORY_MAX_ENTRIES,)
        ).fetchall()
        _history = [
            {"id": r[0], "timestamp": r[1], "save_name": r[2], "summary": r[3], "priority_1": r[4]}
            for r in reversed(rows)
        ]
    except Exception as e:
        logger.warning("Failed to load history: %s", e)


# Load on import
_load_cached()


def broadcast_event(event_type: str, data: dict):
    """Send an SSE event to all connected dashboard clients."""
    for queue in _sse_subscribers:
        queue.put_nowait({"event": event_type, "data": json.dumps(data)})


def update_state(state_dict: dict):
    """Called by the pipeline when new game state is parsed."""
    global _current_state
    _current_state = state_dict
    broadcast_event("state", state_dict)
    try:
        _db_set("state", json.dumps(state_dict))
    except Exception as e:
        logger.warning("Failed to persist state: %s", e)


def update_advice(advice: AdviceResponse, state_summary: str = "", save_name: str = ""):
    """Called by the pipeline when new advice is generated."""
    global _current_advice
    _current_advice = advice
    advice_dict = advice.model_dump(exclude={"raw_text"})
    broadcast_event("advice", advice_dict)
    try:
        _db_set("advice", json.dumps(advice_dict))
    except Exception as e:
        logger.warning("Failed to persist advice: %s", e)

    # Add to history with full state + advice snapshot (ISO format for client-side local time)
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    summary = state_summary or advice.situation[:80] if advice.situation else "State updated"
    entry = {
        "timestamp": ts,
        "save_name": save_name,
        "summary": summary,
        "priority_1": advice.priority_1,
    }
    try:
        db = _get_db()
        cur = db.execute(
            "INSERT INTO history (timestamp, save_name, summary, priority_1, state_json, advice_json) VALUES (?, ?, ?, ?, ?, ?)",
            (ts, save_name, summary, advice.priority_1,
             json.dumps(_current_state) if _current_state else None,
             json.dumps(advice_dict)),
        )
        entry["id"] = cur.lastrowid
        db.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT ?)", (HISTORY_MAX_ENTRIES,))
        db.commit()
    except Exception as e:
        logger.warning("Failed to persist history: %s", e)
    _history.append(entry)
    while len(_history) > HISTORY_MAX_ENTRIES:
        _history.pop(0)


def update_trajectory(entry_id: int, label: str, score: float, reasoning: str,
                      strengths: list[str], risks: list[str], embedding: list[float] | None = None):
    """Update a history entry with trajectory analysis and embedding."""
    try:
        db = _get_db()
        db.execute(
            """UPDATE history SET trajectory_label=?, trajectory_score=?, trajectory_reasoning=?,
               trajectory_strengths=?, trajectory_risks=?, embedding=? WHERE id=?""",
            (label, score, reasoning,
             json.dumps(strengths), json.dumps(risks),
             json.dumps(embedding) if embedding else None, entry_id),
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to update trajectory: %s", e)


def get_last_history_id() -> int | None:
    """Return the ID of the most recent history entry."""
    db = _get_db()
    row = db.execute("SELECT id FROM history ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else None


# -- REST API --

@router.get("/api/health")
async def health():
    return {"status": "ok", "service": "manor-lords-advisor"}


@router.get("/api/state")
async def get_state():
    if _current_state is None:
        return {"status": "waiting", "message": "No game state parsed yet. Save your game."}
    return _current_state


@router.get("/api/advice")
async def get_advice():
    if _current_advice is None:
        return {"status": "waiting", "message": "No advice generated yet. Save your game."}
    return _current_advice.model_dump(exclude={"raw_text"})


@router.get("/api/history")
async def get_history():
    return {"entries": _history}


@router.get("/api/history/{entry_id}")
async def get_history_entry(entry_id: int):
    """Retrieve full state + advice snapshot for a history entry."""
    db = _get_db()
    row = db.execute(
        "SELECT id, timestamp, save_name, summary, priority_1, state_json, advice_json FROM history WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if not row:
        return {"status": "error", "message": "Entry not found"}
    return {
        "id": row[0],
        "timestamp": row[1],
        "save_name": row[2],
        "summary": row[3],
        "priority_1": row[4],
        "state": json.loads(row[5]) if row[5] else None,
        "advice": json.loads(row[6]) if row[6] else None,
    }


@router.get("/api/trends")
async def get_trends(save_name: str | None = None):
    """Return time-series trend data with forecasts and game path assessment."""
    db = _get_db()
    if save_name:
        rows = db.execute(
            "SELECT id, timestamp, save_name, state_json, trajectory_label, trajectory_score, embedding FROM history WHERE save_name = ? AND state_json IS NOT NULL ORDER BY id ASC",
            (save_name,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, timestamp, save_name, state_json, trajectory_label, trajectory_score, embedding FROM history WHERE state_json IS NOT NULL ORDER BY id ASC"
        ).fetchall()

    points = []
    for row in rows:
        state = json.loads(row[3]) if row[3] else None
        if not state:
            continue
        meta = state.get("meta", {})
        settlement = state.get("settlement", {})
        pop = settlement.get("population", {})
        resources = state.get("resources", {})
        food = resources.get("food", {})
        fuel = resources.get("fuel", {})
        construction = resources.get("construction", {})
        clothing = resources.get("clothing", {})
        production = resources.get("production", {})
        military = state.get("military", {})

        families = (pop.get("families", 0) or 0) or 1
        food_total = food.get("total", 0) or 0
        firewood = fuel.get("firewood", 0) or 0
        workers = pop.get("workers", 0) or 0

        season = meta.get("season", "?")
        season_short = season[:3] if len(season) >= 3 else season

        points.append({
            "id": row[0],
            "timestamp": row[1],
            "save_name": row[2],
            "label": f"Y{meta.get('year', '?')} {season_short}",
            "year": meta.get("year", 0),
            "season": season,
            "day": meta.get("day", 0),
            "approval": settlement.get("approval", 0) or 0,
            "families": pop.get("families", 0) or 0,
            "workers": workers,
            "homeless": pop.get("homeless", 0) or 0,
            "food_total": food_total,
            "firewood": firewood,
            "charcoal": fuel.get("charcoal", 0) or 0,
            "timber": construction.get("timber", 0) or 0,
            "planks": construction.get("planks", 0) or 0,
            "stone": construction.get("stone", 0) or 0,
            "clay": construction.get("clay", 0) or 0,
            "leather": clothing.get("leather", 0) or 0,
            "linen": clothing.get("linen", 0) or 0,
            "shoes": clothing.get("shoes", 0) or 0,
            "cloaks": clothing.get("cloaks", 0) or 0,
            "iron": production.get("iron", 0) or 0,
            "ale": production.get("ale", 0) or 0,
            "regional_wealth": settlement.get("regional_wealth", 0) or 0,
            "development_points": state.get("development_points", 0) or 0,
            "retinue_count": military.get("retinue_count", 0) or 0,
            "bandit_camps_nearby": military.get("bandit_camps_nearby", 0) or 0,
            "alert_count": len(state.get("alerts", [])),
            "trajectory_label": row[4],
            "trajectory_score": row[5],
            # Derived metrics
            "food_per_family": round(food_total / families, 1),
            "firewood_per_family": round(firewood / families, 1),
            "worker_ratio": round(workers / families, 2),
        })

    # Compute forecasts and game path
    from src.analysis.trend_predictor import predict_trends
    predictions = predict_trends(points)

    # RAG: find similar past states for the current state
    similar_states = []
    if _current_state and points:
        current_meta = _current_state.get("meta", {})
        current_pop = _current_state.get("settlement", {}).get("population", {})
        current_embedding_raw = db.execute(
            "SELECT embedding FROM history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        current_embedding = json.loads(current_embedding_raw[0]) if current_embedding_raw and current_embedding_raw[0] else None

        from src.analysis.rag_retriever import find_similar_states
        similar_states = find_similar_states(
            current_embedding=current_embedding,
            current_year=current_meta.get("year", 1),
            current_families=current_pop.get("families", 1),
        )

    return {
        "points": points,
        "forecasts": predictions.get("forecasts", []),
        "slopes": predictions.get("slopes", {}),
        "game_path": predictions.get("game_path"),
        "similar_states": similar_states,
        "count": len(points),
    }


@router.get("/api/logs")
async def get_logs(limit: int = 50):
    """Return recent API request/response logs for debugging."""
    from src.memory.request_log import get_recent_logs
    return {"logs": get_recent_logs(limit)}


@router.get("/api/saves")
async def list_saves():
    """List available .sav files in the save folder."""
    from src.config import SAVE_FOLDER
    saves = []
    save_dir = Path(SAVE_FOLDER)
    if save_dir.exists():
        for f in sorted(save_dir.glob("*.sav"), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.name == "rtsSettings.sav" or f.name.endswith("_descr.sav"):
                continue
            saves.append({
                "name": f.name,
                "modified": f.stat().st_mtime,
                "size": f.stat().st_size,
            })
    return {"saves": saves}


_processing = False


@router.post("/api/process")
async def process_latest(save_name: str | None = None):
    """Trigger the pipeline on the latest (or specified) save file.

    Returns immediately and runs the pipeline in the background.
    Results are pushed to the dashboard via SSE.
    """
    global _processing
    if _processing:
        return {"status": "busy", "message": "Pipeline already running"}

    from src.config import SAVE_FOLDER
    save_dir = Path(SAVE_FOLDER)

    if save_name:
        save_path = save_dir / save_name
    else:
        sav_files = [
            f for f in save_dir.glob("*.sav")
            if f.name != "rtsSettings.sav" and not f.name.endswith("_descr.sav")
        ]
        if not sav_files:
            return {"status": "error", "message": "No save files found"}
        save_path = max(sav_files, key=lambda p: p.stat().st_mtime)

    if not save_path.exists():
        return {"status": "error", "message": f"Save file not found: {save_path.name}"}

    broadcast_event("processing", {"save": save_path.name})
    _processing = True
    asyncio.create_task(_run_pipeline(save_path))
    return {"status": "ok", "save": save_path.name, "message": "Pipeline started"}


async def _run_pipeline(save_path: Path):
    """Run the pipeline in the background, broadcasting results via SSE."""
    global _processing
    try:
        from src.pipeline import process_save, load_guides, _guide_context
        if not _guide_context:
            load_guides()
        await process_save(save_path)
    except Exception as e:
        logger.error("Background pipeline failed: %s", e)
        broadcast_event("error", {"message": str(e)})
    finally:
        _processing = False


@router.post("/api/upload")
async def upload_save(file: UploadFile = File(...)):
    """Accept a .sav file upload and run the pipeline on it."""
    global _processing
    if _processing:
        return {"status": "busy", "message": "Pipeline already running"}

    if not file.filename or not file.filename.endswith(".sav"):
        return {"status": "error", "message": "Only .sav files are accepted"}

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_path = tmp_dir / file.filename
    tmp_path.write_bytes(await file.read())

    broadcast_event("processing", {"save": file.filename})
    _processing = True
    asyncio.create_task(_run_pipeline(tmp_path))
    return {"status": "ok", "save": file.filename, "message": "Pipeline started"}


# -- SSE Stream --

@router.get("/api/stream")
async def stream(request: Request):
    """Server-sent events stream for real-time dashboard updates."""
    queue: asyncio.Queue = asyncio.Queue()
    _sse_subscribers.append(queue)

    async def event_generator():
        try:
            # Send current state immediately on connect
            if _current_advice is not None:
                yield {
                    "event": "advice",
                    "data": json.dumps(_current_advice.model_dump(exclude={"raw_text"})),
                }
            if _current_state is not None:
                yield {"event": "state", "data": json.dumps(_current_state)}

            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": ""}
        finally:
            _sse_subscribers.remove(queue)

    return EventSourceResponse(event_generator())


# -- Follow-up Questions --

class AskRequest(BaseModel):
    question: str


@router.post("/api/ask")
async def ask_question(req: AskRequest):
    """Handle a follow-up question from the user."""
    if _current_state is None:
        return {"answer": "No game state loaded yet. Save your game first."}

    from src.mapper.schemas import GameState
    from src.strategy.gemini_client import ask_followup

    try:
        state = GameState(**_current_state) if isinstance(_current_state, dict) else _current_state
        answer = await ask_followup(req.question, state)
        return {"answer": answer}
    except Exception as e:
        logger.error("Follow-up question failed: %s", e)
        return {"answer": f"Error generating response: {e}"}
