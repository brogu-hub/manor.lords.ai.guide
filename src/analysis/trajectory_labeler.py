"""LLM-based trajectory labeling — Gemini scores each game state."""

import json
import logging
from dataclasses import dataclass

from google.genai import types

from src.config import GEMINI_API_KEY, FALLBACK_MODEL
from src.mapper.schemas import GameState
from src.strategy.response_parser import AdviceResponse

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryLabel:
    label: str  # "positive" | "negative" | "neutral"
    score: int  # 0-100
    reasoning: str
    key_strengths: list[str]
    key_risks: list[str]


_LABEL_PROMPT = """You are Gerald — a modern engineer transmigrated into a medieval world, serving as a territory lord's advisor. Evaluate this settlement's trajectory using your engineering mind.

Game State:
- Year {year}, {season}, Day {day}
- Families: {families}, Workers: {workers}, Homeless: {homeless}
- Approval: {approval}%
- Food total: {food} (per family: {food_per_family:.1f})
- Firewood: {firewood} (per family: {firewood_per_family:.1f})
- Timber: {timber}, Planks: {planks}, Stone: {stone}
- Regional wealth: {wealth}, Development points: {dev_points}
- Clothing: {cloaks} cloaks, {shoes} shoes
- Military: {retinue} retinue, {bandits} bandit camps nearby
- Alerts: {alerts}

AI Advisor's Assessment: {situation}

Respond in this exact JSON format:
{{
  "label": "positive" or "negative" or "neutral",
  "score": <0-100 integer>,
  "reasoning": "<1-2 sentence explanation>",
  "key_strengths": ["<strength 1>", "<strength 2>"],
  "key_risks": ["<risk 1>", "<risk 2>"]
}}

Scoring guide:
- 80-100: Thriving settlement, growing sustainably
- 60-79: Stable, on a good path but room for improvement
- 40-59: Precarious, some critical needs unmet
- 20-39: Declining, multiple systems failing
- 0-19: Near collapse, immediate intervention needed"""


async def label_trajectory(state: GameState, advice: AdviceResponse) -> TrajectoryLabel:
    """Ask Gemini to label the current game state trajectory."""
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    meta = state.meta
    settlement = state.settlement
    pop = settlement.population if settlement else None
    res = state.resources
    food = res.food if res else None
    fuel = res.fuel if res else None
    construction = res.construction if res else None
    clothing = res.clothing if res else None
    military = state.military

    families = (pop.families if pop else 0) or 1
    food_total = (food.total if food else 0) or 0
    firewood = (fuel.firewood if fuel else 0) or 0

    prompt = _LABEL_PROMPT.format(
        year=meta.year if meta else "?",
        season=meta.season if meta else "?",
        day=meta.day if meta else "?",
        families=pop.families if pop else 0,
        workers=pop.workers if pop else 0,
        homeless=pop.homeless if pop else 0,
        approval=settlement.approval if settlement else 0,
        food=food_total,
        food_per_family=food_total / families,
        firewood=firewood,
        firewood_per_family=firewood / families,
        timber=construction.timber if construction else 0,
        planks=construction.planks if construction else 0,
        stone=construction.stone if construction else 0,
        wealth=settlement.regional_wealth if settlement else 0,
        dev_points=state.development_points or 0,
        cloaks=clothing.cloaks if clothing else 0,
        shoes=clothing.shoes if clothing else 0,
        retinue=military.retinue_count if military else 0,
        bandits=military.bandit_camps_nearby if military else 0,
        alerts=", ".join(state.alerts) if state.alerts else "None",
        situation=advice.situation or "",
    )

    try:
        response = await client.aio.models.generate_content(
            model=FALLBACK_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=1024),
            ),
        )
        # response.text may raise or be None on blocked responses
        try:
            text = response.text or ""
        except Exception:
            text = ""
            for part in (response.candidates or [{}])[0].get("content", {}).get("parts", []):
                text += part.get("text", "")
        if not text.strip():
            raise ValueError("Empty response from Gemini")
        # Strip markdown fences if present
        cleaned = text.strip()
        logger.debug("Raw trajectory response (%d chars): %s", len(cleaned), cleaned[:300])
        if "```" in cleaned:
            # Remove all fence lines
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        # Find the JSON object
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start < 0 or end <= start:
            raise ValueError(f"No JSON found in response ({len(text)} chars): {text[:300]}")
        data = json.loads(cleaned[start:end])
        return TrajectoryLabel(
            label=data.get("label", "neutral"),
            score=int(data.get("score", 50)),
            reasoning=data.get("reasoning", ""),
            key_strengths=data.get("key_strengths", []),
            key_risks=data.get("key_risks", []),
        )
    except Exception as e:
        logger.warning("Trajectory labeling failed: %s", e)
        return TrajectoryLabel(
            label="neutral", score=50,
            reasoning=f"Labeling unavailable: {e}",
            key_strengths=[], key_risks=[],
        )
