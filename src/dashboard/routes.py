"""Dashboard API routes — REST + SSE endpoints."""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.strategy.response_parser import AdviceResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory state shared with the pipeline
_current_state: dict | None = None
_current_advice: AdviceResponse | None = None
_history: list[dict] = []
_sse_subscribers: list[asyncio.Queue] = []


def broadcast_event(event_type: str, data: dict):
    """Send an SSE event to all connected dashboard clients."""
    for queue in _sse_subscribers:
        queue.put_nowait({"event": event_type, "data": json.dumps(data)})


def update_state(state_dict: dict):
    """Called by the pipeline when new game state is parsed."""
    global _current_state
    _current_state = state_dict
    broadcast_event("state", state_dict)


def update_advice(advice: AdviceResponse, state_summary: str = ""):
    """Called by the pipeline when new advice is generated."""
    global _current_advice
    _current_advice = advice
    advice_dict = advice.model_dump(exclude={"raw_text"})
    broadcast_event("advice", advice_dict)

    # Add to history
    from datetime import datetime
    _history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "summary": state_summary or advice.situation[:80] if advice.situation else "State updated",
        "priority_1": advice.priority_1,
    })
    # Keep last 10
    while len(_history) > 10:
        _history.pop(0)


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
