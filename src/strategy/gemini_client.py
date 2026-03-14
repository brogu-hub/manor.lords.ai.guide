"""Gemini API client with fallback chain and dynamic thinking."""

import logging

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, FALLBACK_CHAIN
from src.mapper.schemas import GameState
from src.strategy.thinking_level import get_thinking_budget
from src.strategy.prompts import build_system_prompt, build_user_prompt
from src.strategy.response_parser import AdviceResponse, parse_advice

logger = logging.getLogger(__name__)

# Initialize client — picks up GEMINI_API_KEY from env automatically
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def generate_advice(
    state: GameState,
    session_context: str = "",
    guide_context: str = "",
) -> AdviceResponse:
    """Generate strategic advice for the current game state.

    Tries each model in the fallback chain on rate limit errors.
    """
    client = _get_client()
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(state, session_context, guide_context)
    thinking_budget = get_thinking_budget(state)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=1.0,
        max_output_tokens=1024,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )

    last_error = None
    for model_id in FALLBACK_CHAIN:
        try:
            logger.info("Calling %s (thinking_budget=%d)", model_id, thinking_budget)
            response = client.models.generate_content(
                model=model_id,
                contents=user_prompt,
                config=config,
            )
            logger.info("Response from %s: %d chars", model_id, len(response.text or ""))
            return parse_advice(response.text or "")

        except Exception as e:
            error_str = str(e)
            last_error = e
            # Check for rate limit (429) or quota errors
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning("Rate limited on %s, trying next model...", model_id)
                continue
            # For other errors, don't retry
            logger.error("Error from %s: %s", model_id, error_str)
            raise

    raise RuntimeError(f"All models in fallback chain exhausted. Last error: {last_error}")


async def ask_followup(
    question: str,
    state: GameState,
    session_context: str = "",
) -> str:
    """Ask a follow-up question with the current game state context."""
    client = _get_client()
    system_prompt = build_system_prompt()

    import json
    state_json = json.dumps(state.model_dump(), indent=2)
    prompt = (
        f"Current game state:\n```json\n{state_json}\n```\n\n"
        f"{session_context}\n\n"
        f"Player's question: {question}\n\n"
        f"Answer specifically and concisely, referencing actual game state values."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=1.0,
        max_output_tokens=512,
    )

    for model_id in FALLBACK_CHAIN:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            return response.text or "No response generated."
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                continue
            raise

    return "All models are currently rate limited. Please try again in a moment."
