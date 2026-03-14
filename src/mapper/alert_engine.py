"""Alert engine — evaluates threshold rules against game state."""

import logging
import operator as op
from pathlib import Path

import yaml

from src.mapper.schemas import GameState

logger = logging.getLogger(__name__)

OPERATORS = {
    "lt": op.lt,
    "gt": op.gt,
    "eq": op.eq,
    "lte": op.le,
    "gte": op.ge,
}


def load_alert_rules(config_path: str | Path | None = None) -> list[dict]:
    """Load alert rules from YAML config."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "alert_rules.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def get_field_value(state: GameState, field_path: str):
    """Get a value from GameState using a dotted path."""
    obj = state
    for part in field_path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(part)
        else:
            obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


def evaluate_alerts(state: GameState, rules: list[dict] | None = None) -> list[str]:
    """Evaluate all alert rules against the current game state.

    Returns a list of alert messages for triggered rules, ordered by severity.
    """
    if rules is None:
        rules = load_alert_rules()

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    triggered = []

    for rule in rules:
        field_path = rule.get("field", "")
        operator_name = rule.get("operator", "lt")
        threshold = rule.get("threshold", 0)
        message = rule.get("message", rule.get("name", "Unknown alert"))
        severity = rule.get("severity", "info")

        value = get_field_value(state, field_path)
        if value is None:
            continue

        comparator = OPERATORS.get(operator_name)
        if comparator is None:
            logger.warning("Unknown operator '%s' in rule '%s'", operator_name, rule.get("name"))
            continue

        try:
            if comparator(float(value), float(threshold)):
                triggered.append((severity_order.get(severity, 2), message))
                logger.info("Alert triggered: %s (value=%s, threshold=%s)", rule.get("name"), value, threshold)
        except (ValueError, TypeError):
            continue

    # Sort by severity (critical first)
    triggered.sort(key=lambda x: x[0])
    return [msg for _, msg in triggered]
