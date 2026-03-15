"""Gemini API client with fallback chain, auto model detection, context caching,
request logging, and DeepEval self-healing."""

import json
import logging
import re
import time

from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL,
    CACHE_TTL_SECONDS, MAX_EVAL_RETRIES,
)
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
    """Extract (version, priority) from a model name for sorting."""
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
                ttl=f"{CACHE_TTL_SECONDS}s",
            ),
        )
        _cached_content_name = cache.name
        _cached_model = model_id
        logger.info("Created context cache: %s (model=%s)", cache.name, model_id)
        return cache.name
    except Exception as e:
        logger.warning("Context caching not available for %s: %s", model_id, e)
        return None


def _invalidate_cache():
    """Clear the cached content reference."""
    global _cached_content_name, _cached_model
    _cached_content_name = None
    _cached_model = None


# -- Structural validation (no LLM cost) --

def _has_required_sections(advice: AdviceResponse) -> bool:
    """Quick check that all sections are populated."""
    return all([
        advice.priority_1,
        advice.priority_2,
        advice.priority_3,
        advice.situation,
        advice.next_season,
    ])


def _build_structural_correction(advice: AdviceResponse) -> str:
    """Build a correction prompt for missing sections."""
    missing = []
    if not advice.priority_1:
        missing.append("PRIORITY_1")
    if not advice.priority_2:
        missing.append("PRIORITY_2")
    if not advice.priority_3:
        missing.append("PRIORITY_3")
    if not advice.situation:
        missing.append("SITUATION")
    if not advice.next_season:
        missing.append("NEXT_SEASON")
    if not advice.warnings and not advice.priority_1:
        missing.append("WARNINGS")
    return (
        f"\n\nIMPORTANT CORRECTION: Your previous response was missing these "
        f"required sections: {', '.join(missing)}. You MUST include ALL sections "
        f"in your response: WARNINGS, PRIORITY_1, PRIORITY_2, PRIORITY_3, "
        f"SITUATION, NEXT_SEASON."
    )


# -- Main API calls --

async def generate_advice(
    state: GameState,
    session_context: str = "",
    guide_context: str = "",
) -> AdviceResponse:
    """Generate strategic advice with eval-based self-healing.

    Flow: generate → parse → structural check → DeepEval → retry if needed.
    Max attempts = 1 + MAX_EVAL_RETRIES.
    """
    client = _get_client()
    fallback_chain = _get_fallback_chain()
    system_prompt = build_system_prompt()
    thinking_budget = get_thinking_budget(state)
    state_json = json.dumps(state.model_dump(), indent=2, ensure_ascii=False)
    alerts_list = list(state.alerts) if state.alerts else []

    best_advice: AdviceResponse | None = None
    correction_context = ""

    for attempt in range(1, 2 + MAX_EVAL_RETRIES):
        last_error = None

        for model_id in fallback_chain:
            cache_name = _ensure_cache(client, model_id, system_prompt, guide_context)

            if cache_name:
                user_prompt = build_user_prompt(
                    state, session_context, guide_context="",
                    correction_context=correction_context,
                )
                gen_config = types.GenerateContentConfig(
                    cached_content=cache_name,
                    temperature=1.0,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                )
            else:
                user_prompt = build_user_prompt(
                    state, session_context, guide_context,
                    correction_context=correction_context,
                )
                gen_config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=1.0,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                )

            t0 = time.time()
            try:
                logger.info(
                    "Calling %s (attempt=%d, thinking_budget=%d, cached=%s)",
                    model_id, attempt, thinking_budget, bool(cache_name),
                )
                response = client.models.generate_content(
                    model=model_id,
                    contents=user_prompt,
                    config=gen_config,
                )
                duration_ms = int((time.time() - t0) * 1000)
                response_text = response.text or ""
                logger.info("Response from %s: %d chars in %dms", model_id, len(response_text), duration_ms)

                advice = parse_advice(response_text)
                best_advice = advice

                # Structural pre-check (free, no LLM call)
                if not _has_required_sections(advice):
                    logger.warning("Structural check failed (attempt %d), missing sections", attempt)
                    correction_context = _build_structural_correction(advice)

                    log_request(
                        model=model_id, request_type="advice",
                        system_prompt=system_prompt[:500], user_prompt=user_prompt[:2000],
                        thinking_budget=thinking_budget, temperature=1.0, max_tokens=4096,
                        response_text=response_text, duration_ms=duration_ms,
                        game_year=state.meta.year, game_season=state.meta.season,
                        alerts=alerts_list, eval_passed=False,
                        eval_scores={"structural": 0.0}, attempt=attempt,
                    )
                    break  # Break model loop, retry with correction

                # DeepEval evaluation (uses LLM judge)
                eval_result = _run_eval(response_text, state_json, alerts_list)

                log_request(
                    model=model_id, request_type="advice",
                    system_prompt=system_prompt[:500], user_prompt=user_prompt[:2000],
                    thinking_budget=thinking_budget, temperature=1.0, max_tokens=4096,
                    response_text=response_text, duration_ms=duration_ms,
                    game_year=state.meta.year, game_season=state.meta.season,
                    alerts=alerts_list,
                    eval_passed=eval_result.passed if eval_result else None,
                    eval_scores=eval_result.scores if eval_result else None,
                    eval_reasons=eval_result.reasons if eval_result else None,
                    attempt=attempt,
                )

                if eval_result is None or eval_result.passed:
                    return advice

                # Eval failed — set correction for retry
                logger.warning(
                    "Eval failed (attempt %d): %s",
                    attempt, eval_result.reasons,
                )
                correction_context = eval_result.retry_prompt or ""
                break  # Break model loop, retry with correction

            except Exception as e:
                duration_ms = int((time.time() - t0) * 1000)
                error_str = str(e)
                last_error = e

                log_request(
                    model=model_id, request_type="advice",
                    system_prompt=system_prompt[:500], user_prompt=user_prompt[:2000],
                    thinking_budget=thinking_budget, temperature=1.0, max_tokens=4096,
                    duration_ms=duration_ms, error=error_str[:1000],
                    game_year=state.meta.year, game_season=state.meta.season,
                    alerts=alerts_list, attempt=attempt,
                )

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning("Rate limited on %s, trying next model...", model_id)
                    continue
                if cache_name and ("cache" in error_str.lower() or "cached_content" in error_str.lower()):
                    _invalidate_cache()
                    logger.warning("Cache error on %s, retrying without cache...", model_id)
                    continue
                logger.error("Error from %s: %s", model_id, error_str)
                raise
        else:
            # Model loop exhausted without break (all rate limited)
            if last_error:
                raise RuntimeError(f"All models exhausted. Last error: {last_error}")

    # Return best attempt (last successful parse)
    if best_advice:
        return best_advice
    raise RuntimeError("Failed to generate advice after all attempts")


def _run_eval(response_text: str, state_json: str, alerts: list[str]):
    """Run DeepEval evaluation, returning EvalResult or None on import/init error."""
    try:
        from src.strategy.evaluator import evaluate_response
        return evaluate_response(response_text, state_json, alerts)
    except ImportError:
        logger.warning("DeepEval not available, skipping evaluation")
        return None
    except Exception as e:
        logger.warning("Evaluation failed: %s", e)
        return None


_FOLLOWUP_SYSTEM = (
    "You are a Manor Lords expert advisor answering the player's follow-up questions. "
    "Respond conversationally and directly — answer the question asked. "
    "Do NOT use the structured WARNINGS/PRIORITY format. "
    "Be specific: reference actual numbers, building names, and game mechanics. "
    "Keep answers concise (2-4 paragraphs max)."
)


async def ask_followup(
    question: str,
    state: GameState,
    session_context: str = "",
) -> str:
    """Ask a follow-up question with the current game state context."""
    client = _get_client()
    fallback_chain = _get_fallback_chain()

    state_json = json.dumps(state.model_dump(), indent=2)
    prompt = (
        f"Current game state:\n```json\n{state_json}\n```\n\n"
        f"{session_context}\n\n"
        f"Player's question: {question}"
    )

    config = types.GenerateContentConfig(
        system_instruction=_FOLLOWUP_SYSTEM,
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
                model=model_id, request_type="followup",
                system_prompt=_FOLLOWUP_SYSTEM, user_prompt=prompt[:2000],
                temperature=1.0, max_tokens=512,
                response_text=response_text, duration_ms=duration_ms,
                game_year=state.meta.year, game_season=state.meta.season,
            )

            return response_text
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            error_str = str(e)

            log_request(
                model=model_id, request_type="followup",
                system_prompt=_FOLLOWUP_SYSTEM, user_prompt=prompt[:2000],
                temperature=1.0, max_tokens=512,
                duration_ms=duration_ms, error=error_str[:1000],
                game_year=state.meta.year, game_season=state.meta.season,
            )

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                continue
            raise

    return "All models are currently rate limited. Please try again in a moment."
