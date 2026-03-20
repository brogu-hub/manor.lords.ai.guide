"""Prompt management for the Manor Lords advisor."""

import json
from pathlib import Path

import yaml

from src.mapper.schemas import GameState


def load_prompt_config(config_path: str | Path | None = None) -> dict:
    """Load the advisor prompt config from YAML."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "advisor_prompt.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_system_prompt(config: dict | None = None) -> str:
    """Build the system prompt for the advisor."""
    if config is None:
        config = load_prompt_config()
    return config.get("system_prompt", "You are a Manor Lords strategic advisor.")


def build_user_prompt(
    state: GameState,
    session_context: str = "",
    guide_context: str = "",
    correction_context: str = "",
    config: dict | None = None,
) -> str:
    """Build the user prompt with game state and context injected."""
    if config is None:
        config = load_prompt_config()

    template = config.get("user_prompt_template", "Game state: {game_state_json}")

    state_json = json.dumps(state.model_dump(), indent=2, ensure_ascii=False)

    game_version = state.meta.game_version or "unknown"

    prompt = template.format(
        game_state_json=state_json,
        game_version=game_version,
        session_context=session_context or "No previous session data available.",
        guide_context=guide_context or "",
    )

    if correction_context:
        prompt += correction_context

    return prompt
