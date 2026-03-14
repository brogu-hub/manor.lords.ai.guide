"""Dynamic thinking level/budget based on game state complexity."""

from src.mapper.schemas import GameState

# Thinking budgets for Gemini 2.5 models (token count)
THINKING_BUDGETS = {
    "minimal": 0,      # No thinking — fast, cheap
    "low": 512,         # Light reasoning
    "medium": 2048,     # Moderate reasoning
    "high": 8192,       # Full reasoning
}


def get_thinking_budget(state: GameState) -> int:
    """Determine thinking budget based on game state complexity.

    Returns a token budget for the thinking_config.
    """
    alerts_count = len(state.alerts)
    year = state.meta.year

    if alerts_count == 0 and year < 3:
        return THINKING_BUDGETS["minimal"]
    if alerts_count <= 1:
        return THINKING_BUDGETS["low"]
    if alerts_count <= 3:
        return THINKING_BUDGETS["medium"]
    return THINKING_BUDGETS["high"]
