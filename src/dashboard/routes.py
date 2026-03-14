"""Dashboard API routes — REST + SSE endpoints."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
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


# -- HTML --

@router.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent.parent.parent / "static" / "index.html"
    return html_path.read_text(encoding="utf-8")


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
