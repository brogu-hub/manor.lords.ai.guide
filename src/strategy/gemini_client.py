"""Gemini API client with fallback chain, auto model detection, and dynamic thinking."""

import logging
import re

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL
from src.mapper.schemas import GameState
from src.strategy.thinking_level import get_thinking_budget
from src.strategy.prompts import build_system_prompt, build_user_prompt
from src.strategy.response_parser import AdviceResponse, parse_advice

logger = logging.getLogger(__name__)

_client: genai.Client | None = None
_resolved_chain: list[str] | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _parse_version(name: str) -> tuple[float, int]:
    """Extract (version, priority) from a model name for sorting.

    Higher version = better. Among same version, prefer:
      flash > flash-lite > preview variants
    """
    # Extract version like "3.1", "2.5", "2.0"
    m = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name)
    if not m:
        return (0.0, 0)
    version = float(m.group(1))
    # Prefer non-lite over lite, non-preview over preview
    priority = 10
    if "lite" in name:
        priority -= 2
    if "preview" in name:
        priority -= 1
    if "image" in name or "audio" in name or "tts" in name:
        priority -= 5  # deprioritize specialized models
    return (version, priority)


def _detect_best_model() -> str:
    """Query the API for available models and pick the best flash model."""
    client = _get_client()
    candidates = []
    for model in client.models.list():
        name = model.name.replace("models/", "")
        # Only consider flash models, skip specialized ones
        if "flash" not in name:
            continue
        if any(kw in name for kw in ["image", "audio", "tts", "native"]):
            continue
        # Skip bare aliases like "gemini-flash-latest"
        if not re.search(r"gemini-\d", name):
            continue
        candidates.append(name)

    if not candidates:
        logger.warning("No flash models found via API, using fallback: %s", FALLBACK_MODEL)
        return FALLBACK_MODEL

    # Sort by version (descending), then priority (descending)
    candidates.sort(key=_parse_version, reverse=True)
    best = candidates[0]
    logger.info("Auto-detected best model: %s (from %d candidates)", best, len(candidates))
    return best


def _get_fallback_chain() -> list[str]:
    """Build the fallback chain, resolving 'auto' if needed."""
    global _resolved_chain
    if _resolved_chain is not None:
        return _resolved_chain

    if PRIMARY_MODEL == "auto":
        primary = _detect_best_model()
    else:
        primary = PRIMARY_MODEL

    # Build chain: primary → fallback (skip duplicates)
    chain = [primary]
    if FALLBACK_MODEL != primary:
        chain.append(FALLBACK_MODEL)
    _resolved_chain = chain
    logger.info("Model fallback chain: %s", chain)
    return chain


async def generate_advice(
    state: GameState,
    session_context: str = "",
    guide_context: str = "",
) -> AdviceResponse:
    """Generate strategic advice for the current game state.

    Tries each model in the fallback chain on rate limit errors.
    """
    client = _get_client()
    fallback_chain = _get_fallback_chain()
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(state, session_context, guide_context)
    thinking_budget = get_thinking_budget(state)

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=1.0,
        max_output_tokens=4096,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )

    last_error = None
    for model_id in fallback_chain:
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
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning("Rate limited on %s, trying next model...", model_id)
                continue
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
    fallback_chain = _get_fallback_chain()
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

    for model_id in fallback_chain:
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
