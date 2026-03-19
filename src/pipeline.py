"""Pipeline orchestrator — ties all components together.

Flow: parse save → map state → evaluate alerts → load context → generate advice →
      broadcast → label trajectory → embed state
"""

import asyncio
import logging
from pathlib import Path

from src.parser.gvas_parser import parse_save
from src.mapper.state_mapper import map_state
from src.mapper.alert_engine import evaluate_alerts
from src.strategy.gemini_client import generate_advice
from src.memory.session_store import save_entry, get_session_context
from src.memory.request_log import init_db
from src.guides.steam_notes import (
    update_guide_cache, get_patch_context,
    update_workshop_guides, get_workshop_context,
)
from src.dashboard.routes import (
    update_state, update_advice, broadcast_event,
    update_trajectory, get_last_history_id,
)

logger = logging.getLogger(__name__)

# Guide context is loaded once at startup
_guide_context: str = ""


def load_guides():
    """Load all guide markdown files and Steam patch notes into context."""
    global _guide_context

    # Initialise request log DB
    init_db()

    # Load static guides
    guides_dir = Path(__file__).parent.parent / "guides"
    parts = []
    md_count = 0
    if guides_dir.exists():
        parts.append("REFERENCE MATERIAL — Manor Lords Strategy Guides:\n")
        for guide_file in sorted(guides_dir.glob("*.md")):
            content = guide_file.read_text(encoding="utf-8")
            parts.append(f"\n--- {guide_file.stem.replace('_', ' ').title()} ---\n{content}")
            md_count += 1

    # Fetch latest Steam patch notes
    try:
        new_count = update_guide_cache()
        patch_context = get_patch_context()
        if patch_context:
            parts.append(patch_context)
        logger.info("Patch notes: %d new fetched", new_count)
    except Exception as e:
        logger.warning("Failed to load patch notes: %s", e)

    # Fetch Steam Workshop guides
    try:
        ws_count = update_workshop_guides()
        ws_context = get_workshop_context()
        if ws_context:
            parts.append(ws_context)
        logger.info("Workshop guides: %d new fetched", ws_count)
    except Exception as e:
        logger.warning("Failed to load Workshop guides: %s", e)

    _guide_context = "\n".join(parts)
    logger.info("Loaded %d guide files + patch notes (%d chars total)", md_count, len(_guide_context))


async def process_save(save_path: str | Path):
    """Full pipeline: parse a save file and generate advice.

    This is the main entry point called by the file watcher.
    """
    save_path = Path(save_path)
    logger.info("Processing save: %s", save_path.name)

    # Step 1: Parse .sav → raw JSON
    try:
        raw_json = parse_save(save_path)
    except Exception as e:
        logger.error("Failed to parse save file: %s", e)
        return

    # Step 2: Map raw JSON → GameState
    try:
        state = map_state(raw_json)
    except Exception as e:
        logger.error("Failed to map game state: %s", e)
        return

    # Step 3: Evaluate alerts
    alerts = evaluate_alerts(state)
    state.alerts = alerts

    # Step 4: Broadcast state to dashboard
    state_dict = state.model_dump()
    update_state(state_dict)
    logger.info(
        "State: Year %d %s, Food %.0f, Approval %.0f, Alerts: %d",
        state.meta.year, state.meta.season,
        state.resources.food.total, state.settlement.approval,
        len(alerts),
    )

    # Step 5: Get session context
    session_context = get_session_context()

    # Step 6: Generate advice via Gemini (streaming)
    try:
        def on_chunk(text, is_thinking=False, attempt=1):
            event_type = "thinking_chunk" if is_thinking else "advice_chunk"
            broadcast_event(event_type, {"text": text, "attempt": attempt})

        broadcast_event("streaming_start", {})
        result = await generate_advice(
            state, session_context, _guide_context, on_chunk=on_chunk,
        )
        advice = result.advice
        broadcast_event("streaming_end", {})

        # Broadcast eval results
        if result.eval_scores is not None:
            broadcast_event("eval_result", {
                "passed": result.eval_passed,
                "scores": result.eval_scores,
                "reasons": result.eval_reasons or {},
                "attempt": result.attempt,
            })
    except Exception as e:
        logger.error("Failed to generate advice: %s", e)
        broadcast_event("streaming_end", {})
        return

    # Step 7: Broadcast advice to dashboard
    state_summary = f"Year {state.meta.year} {state.meta.season}"
    update_advice(advice, state_summary, save_name=save_path.name)

    # Step 8: Label trajectory + embed state (concurrent, non-blocking)
    history_id = get_last_history_id()
    if history_id:
        try:
            from src.analysis.trajectory_labeler import label_trajectory
            from src.analysis.state_embedder import embed_state

            label_result, embedding = await asyncio.gather(
                label_trajectory(state, advice),
                embed_state(state),
                return_exceptions=True,
            )

            if isinstance(label_result, Exception):
                logger.warning("Trajectory labeling failed: %s", label_result)
                label_result = None
            if isinstance(embedding, Exception):
                logger.warning("State embedding failed: %s", embedding)
                embedding = None

            if label_result:
                update_trajectory(
                    entry_id=history_id,
                    label=label_result.label,
                    score=label_result.score,
                    reasoning=label_result.reasoning,
                    strengths=label_result.key_strengths,
                    risks=label_result.key_risks,
                    embedding=embedding,
                )
                logger.info(
                    "Trajectory: %s (score=%d) | Embedded: %s",
                    label_result.label, label_result.score,
                    "yes" if embedding else "no",
                )
        except Exception as e:
            logger.warning("Analysis step failed: %s", e)

    # Step 9: Save to session history
    save_entry(
        state_summary={
            "year": state.meta.year,
            "season": state.meta.season,
            "food": state.resources.food.total,
            "approval": state.settlement.approval,
            "population": state.settlement.population.families,
            "alerts": alerts,
        },
        advice_summary=advice.priority_1,
    )

    logger.info("Pipeline complete — advice delivered")
