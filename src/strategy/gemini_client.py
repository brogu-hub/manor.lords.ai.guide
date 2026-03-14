"""Gemini API client with fallback chain, auto model detection, context caching, and request logging."""

import json
import logging
import re
import time

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL
from src.mapper.schemas import GameState
from src.memory.request_log import log_request
from src.strategy.thinking_level import get_thinking_budget
from src.strategy.prompts import build_system_prompt, build_user_prompt
from src.strategy.response_parser import AdviceResponse, parse_advice

logger = logging.getLogger(__name__)

_client: genai.Client | None = None
_resolved_chain: list[str] | None = None
_cached_content_name: str | None = None
_cached_model: str | None = None


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
    m = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name)
    if not m:
        return (0.0, 0)
    version = float(m.group(1))
    priority = 10
    if "lite" in name:
        priority -= 2
    if "preview" in name:
        priority -= 1
    if "image" in name or "audio" in name or "tts" in name:
        priority -= 5
    return (version, priority)


def _detect_best_model() -> str:
    """Query the API for available models and pick the best flash model."""
    client = _get_client()
    candidates = []
    for model in client.models.list():
        name = model.name.replace("models/", "")
        if "flash" not in name:
            continue
        if any(kw in name for kw in ["image", "audio", "tts", "native"]):
            continue
        if not re.search(r"gemini-\d", name):
            continue
        candidates.append(name)

    if not candidates:
        logger.warning("No flash models found via API, using fallback: %s", FALLBACK_MODEL)
        return FALLBACK_MODEL

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

    chain = [primary]
    if FALLBACK_MODEL != primary:
        chain.append(FALLBACK_MODEL)
    _resolved_chain = chain
    logger.info("Model fallback chain: %s", chain)
    return chain


# -- Context Cache --

def _ensure_cache(
    client: genai.Client,
    model_id: str,
    system_prompt: str,
    guide_context: str,
) -> str | None:
    """Create or reuse a Gemini context cache for system prompt + guides."""
    global _cached_content_name, _cached_model

    if _cached_content_name and _cached_model == model_id:
        return _cached_content_name

    if not guide_context:
        return None

    try:
        cache = client.caches.create(
            model=model_id,
            config=types.CreateCachedContentConfig(
                display_name="manor-lords-advisor",
                system_instruction=system_prompt,
                contents=[guide_context],
                ttl="1800s",  # 30 minutes
            ),
        )
        _cached_content_name = cache.name
        _cached_model = model_id
        logger.info("Created context cache: %s (model=%s)", cache.name, model_id)
        return cache.name
    except Exception as e:
        logger.warning("Context caching not available for %s: %s", model_id, e)
        return None


async def generate_advice(
    state: GameState,
    session_context: str = "",
    guide_context: str = "",
) -> AdviceResponse:
    """Generate strategic advice for the current game state.

    Tries each model in the fallback chain on rate limit errors.
    Uses context caching for system prompt + guides when available.
    """
    client = _get_client()
    fallback_chain = _get_fallback_chain()
    system_prompt = build_system_prompt()
    thinking_budget = get_thinking_budget(state)

    last_error = None
    for model_id in fallback_chain:
        # Try context cache for this model
        cache_name = _ensure_cache(client, model_id, system_prompt, guide_context)

        if cache_name:
            # Cached: guide context is in the cache, don't include in prompt
            user_prompt = build_user_prompt(state, session_context, guide_context="")
            config = types.GenerateContentConfig(
                cached_content=cache_name,
                temperature=1.0,
                max_output_tokens=4096,
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            )
        else:
            # No cache: inline everything
            user_prompt = build_user_prompt(state, session_context, guide_context)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=1.0,
                max_output_tokens=4096,
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
            )

        t0 = time.time()
        try:
            logger.info(
                "Calling %s (thinking_budget=%d, cached=%s)",
                model_id, thinking_budget, bool(cache_name),
            )
            response = client.models.generate_content(
                model=model_id,
                contents=user_prompt,
                config=config,
            )
            duration_ms = int((time.time() - t0) * 1000)
            response_text = response.text or ""
            logger.info("Response from %s: %d chars in %dms", model_id, len(response_text), duration_ms)

            log_request(
                model=model_id,
                request_type="advice",
                system_prompt=system_prompt[:500],
                user_prompt=user_prompt[:2000],
                thinking_budget=thinking_budget,
                temperature=1.0,
                max_tokens=4096,
                response_text=response_text,
                duration_ms=duration_ms,
                game_year=state.meta.year,
                game_season=state.meta.season,
                alerts=[a for a in state.alerts] if state.alerts else None,
            )

            return parse_advice(response_text)

        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            error_str = str(e)
            last_error = e

            log_request(
                model=model_id,
                request_type="advice",
                system_prompt=system_prompt[:500],
                user_prompt=user_prompt[:2000],
                thinking_budget=thinking_budget,
                temperature=1.0,
                max_tokens=4096,
                duration_ms=duration_ms,
                error=error_str[:1000],
                game_year=state.meta.year,
                game_season=state.meta.season,
                alerts=[a for a in state.alerts] if state.alerts else None,
            )

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning("Rate limited on %s, trying next model...", model_id)
                continue
            # If cache-related error, invalidate and retry without cache
            if cache_name and ("cache" in error_str.lower() or "cached_content" in error_str.lower()):
                global _cached_content_name, _cached_model
                _cached_content_name = None
                _cached_model = None
                logger.warning("Cache error on %s, retrying without cache...", model_id)
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
        t0 = time.time()
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            duration_ms = int((time.time() - t0) * 1000)
            response_text = response.text or "No response generated."

            log_request(
                model=model_id,
                request_type="followup",
                system_prompt=system_prompt[:500],
                user_prompt=prompt[:2000],
                temperature=1.0,
                max_tokens=512,
                response_text=response_text,
                duration_ms=duration_ms,
                game_year=state.meta.year,
                game_season=state.meta.season,
            )

            return response_text
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            error_str = str(e)

            log_request(
                model=model_id,
                request_type="followup",
                system_prompt=system_prompt[:500],
                user_prompt=prompt[:2000],
                temperature=1.0,
                max_tokens=512,
                duration_ms=duration_ms,
                error=error_str[:1000],
                game_year=state.meta.year,
                game_season=state.meta.season,
            )

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                continue
            raise

    return "All models are currently rate limited. Please try again in a moment."
