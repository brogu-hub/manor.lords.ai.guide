"""DeepEval-based response evaluator for LLM advice quality."""

import json
import logging
from dataclasses import dataclass, field

from deepeval.models import GeminiModel
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from src.config import GEMINI_API_KEY, EVAL_THRESHOLD

logger = logging.getLogger(__name__)

_judge_model: GeminiModel | None = None
_metrics: dict[str, GEval] = {}


@dataclass
class EvalResult:
    """Result of evaluating an LLM response."""
    passed: bool
    scores: dict[str, float] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)
    retry_prompt: str | None = None


def init_evaluator(model_name: str = "gemini-2.5-flash"):
    """Initialise the DeepEval judge model and metrics."""
    global _judge_model, _metrics

    _judge_model = GeminiModel(
        model_name=model_name,
        api_key=GEMINI_API_KEY,
        temperature=0,
    )

    _metrics["format"] = GEval(
        name="format_compliance",
        criteria=(
            "Check that the response contains ALL of these required sections with "
            "substantive content (not empty): WARNINGS, PRIORITY_1, PRIORITY_2, "
            "PRIORITY_3, SITUATION, NEXT_SEASON. Each section should have at least "
            "one meaningful sentence."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=_judge_model,
        async_mode=False,
    )

    _metrics["specificity"] = GEval(
        name="specificity",
        criteria=(
            "Check that the advice references specific game state values such as "
            "exact resource counts, building names, family counts, or approval "
            "numbers. Vague advice like 'build more food buildings' should score "
            "low. Specific advice like 'Build a Forager Hut — you have 0 food and "
            "5 idle families' should score high."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=EVAL_THRESHOLD,
        model=_judge_model,
        async_mode=False,
    )

    _metrics["relevance"] = GEval(
        name="state_relevance",
        criteria=(
            "Check that the advice addresses the most critical issues shown in the "
            "game state input. If there are starvation or food alerts, the advice "
            "MUST prioritize food production. If there are fuel alerts, it must "
            "address firewood or charcoal. The advice should not ignore critical "
            "alerts in favour of low-priority improvements."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=EVAL_THRESHOLD,
        model=_judge_model,
        async_mode=False,
    )

    logger.info("DeepEval evaluator initialised with model %s", model_name)


def evaluate_response(
    response_text: str,
    game_state_json: str,
    alerts: list[str],
) -> EvalResult:
    """Evaluate an LLM response using all configured metrics.

    Returns an EvalResult with pass/fail status, scores, and a correction
    prompt if the response failed evaluation.
    """
    if not _metrics:
        init_evaluator()

    # Build context input for metrics that need it
    context_input = f"Game state:\n{game_state_json}\n\nAlerts: {json.dumps(alerts)}"

    test_case = LLMTestCase(
        input=context_input,
        actual_output=response_text,
    )

    scores = {}
    reasons = {}
    all_passed = True

    for name, metric in _metrics.items():
        try:
            metric.measure(test_case)
            scores[name] = metric.score
            reasons[name] = metric.reason or ""
            if metric.score < metric.threshold:
                all_passed = False
                logger.info("Eval %s: %.2f (FAIL, threshold=%.2f) — %s",
                            name, metric.score, metric.threshold, metric.reason)
            else:
                logger.info("Eval %s: %.2f (PASS)", name, metric.score)
        except Exception as e:
            logger.warning("Eval metric %s failed: %s", name, e)
            scores[name] = 0.0
            reasons[name] = f"Evaluation error: {e}"
            all_passed = False

    result = EvalResult(passed=all_passed, scores=scores, reasons=reasons)

    if not all_passed:
        result.retry_prompt = _build_correction_prompt(scores, reasons)

    return result


def _build_correction_prompt(
    scores: dict[str, float],
    reasons: dict[str, str],
) -> str:
    """Build a correction prompt from failed evaluation metrics."""
    parts = [
        "\n\nIMPORTANT — Your previous response failed quality review. "
        "Fix these issues:"
    ]

    for name, score in scores.items():
        metric = _metrics.get(name)
        if metric and score < metric.threshold:
            parts.append(f"- {name} (score {score:.2f}): {reasons.get(name, 'No details')}")

    parts.append(
        "\nYou MUST respond using the exact format: WARNINGS, PRIORITY_1, "
        "PRIORITY_2, PRIORITY_3, SITUATION, NEXT_SEASON. "
        "Reference specific numbers from the game state."
    )

    return "\n".join(parts)
