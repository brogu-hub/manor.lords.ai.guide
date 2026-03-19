"""Gemini embedding API for game state vectors."""

import logging

from src.config import GEMINI_API_KEY
from src.mapper.schemas import GameState

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"


def _state_to_text(state: GameState) -> str:
    """Convert a game state to a text summary for embedding."""
    meta = state.meta
    settlement = state.settlement
    pop = settlement.population if settlement else None
    res = state.resources
    food = res.food if res else None
    fuel = res.fuel if res else None
    construction = res.construction if res else None
    military = state.military

    families = (pop.families if pop else 0) or 1
    food_total = (food.total if food else 0) or 0
    firewood = (fuel.firewood if fuel else 0) or 0

    parts = [
        f"Year {meta.year if meta else '?'} {meta.season if meta else '?'}",
        f"{pop.families if pop else 0} families {pop.workers if pop else 0} workers",
        f"food {food_total:.0f} per_family {food_total / families:.1f}",
        f"firewood {firewood:.0f} per_family {firewood / families:.1f}",
        f"approval {settlement.approval if settlement else 0:.0f}%",
        f"timber {construction.timber if construction else 0:.0f}",
        f"stone {construction.stone if construction else 0:.0f}",
        f"wealth {settlement.regional_wealth if settlement else 0:.0f}",
        f"dev_points {state.development_points or 0}",
        f"retinue {military.retinue_count if military else 0}",
        f"bandits {military.bandit_camps_nearby if military else 0}",
        f"alerts {len(state.alerts) if state.alerts else 0}",
    ]
    return " | ".join(parts)


async def embed_state(state: GameState) -> list[float] | None:
    """Create a 768-dim vector embedding of the game state."""
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)
    text = _state_to_text(state)

    try:
        result = await client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        vector = result.embeddings[0].values
        logger.info("Embedded state (%d dims)", len(vector))
        return list(vector)
    except Exception as e:
        logger.warning("State embedding failed: %s", e)
        return None
