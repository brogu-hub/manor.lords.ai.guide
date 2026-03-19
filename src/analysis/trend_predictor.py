"""NumPy-based trend prediction for game state metrics."""

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Metrics to forecast with their display names and weights for game path scoring
FORECAST_METRICS = {
    "food_per_family": {"name": "Food sustainability", "weight": 0.30, "good": 8, "warn": 4},
    "approval": {"name": "Approval", "weight": 0.25, "good": 70, "warn": 50},
    "firewood_per_family": {"name": "Fuel supply", "weight": 0.15, "good": 5, "warn": 2},
    "worker_ratio": {"name": "Workforce efficiency", "weight": 0.15, "good": 0.6, "warn": 0.3},
    "regional_wealth": {"name": "Economy", "weight": 0.15, "good": None, "warn": None},
}

SEASONS = ["Spring", "Summer", "Autumn", "Winter"]


def _next_season_label(last_point: dict) -> str:
    """Generate the label for the next predicted season."""
    year = last_point.get("year", 1)
    season = last_point.get("season", "Spring")
    idx = SEASONS.index(season) if season in SEASONS else 0
    if idx == 3:
        return f"Y{year + 1} {SEASONS[0][:3]}*"
    return f"Y{year} {SEASONS[idx + 1][:3]}*"


def predict_trends(points: list[dict]) -> dict:
    """Compute linear regression forecasts and game path assessment.

    Args:
        points: Flat list of trend data points (from /api/trends extraction).

    Returns:
        Dict with forecasts, slopes, and game_path assessment.
    """
    result = {"forecasts": [], "slopes": {}, "game_path": None}

    if len(points) < 2:
        # Not enough data for trends — only compute current snapshot game path
        if points:
            result["game_path"] = _score_game_path_snapshot(points[-1])
        return result

    x = np.arange(len(points), dtype=float)
    n = len(points)

    # Compute slopes and forecasts for each metric
    forecast_point = {}
    for metric, info in FORECAST_METRICS.items():
        values = [p.get(metric, 0) or 0 for p in points]
        y = np.array(values, dtype=float)

        if len(points) >= 3:
            # Use last N points for regression (max 10 for responsiveness)
            window = min(n, 10)
            x_win = x[-window:]
            y_win = y[-window:]
            slope, intercept = np.polyfit(x_win, y_win, 1)
            predicted = slope * (x_win[-1] + 1) + intercept
        else:
            slope = float(y[-1] - y[0]) / max(n - 1, 1)
            predicted = float(y[-1]) + slope

        result["slopes"][metric] = round(float(slope), 3)
        forecast_point[metric] = round(max(float(predicted), 0), 1)

    if points:
        forecast_point["label"] = _next_season_label(points[-1])
        result["forecasts"] = [forecast_point]

    # Game path scoring
    if len(points) >= 3:
        result["game_path"] = _score_game_path(points[-1], result["slopes"])
    else:
        result["game_path"] = _score_game_path_snapshot(points[-1])

    return result


def _score_game_path(current: dict, slopes: dict) -> dict:
    """Score game path using both current values and trend slopes."""
    total_score = 0
    factors = []

    for metric, info in FORECAST_METRICS.items():
        val = current.get(metric, 0) or 0
        slope = slopes.get(metric, 0)

        # Determine direction
        if abs(slope) < 0.1:
            direction = "stable"
        elif slope > 0:
            direction = "rising"
        else:
            direction = "falling"

        # Score this metric (0-100)
        if info["good"] is not None:
            if val >= info["good"] or (direction == "rising" and val >= info["warn"]):
                metric_score = 100
                status = "good"
            elif val >= info["warn"] or direction == "stable":
                metric_score = 50
                status = "warning"
            else:
                metric_score = max(0, (val / info["warn"]) * 50) if info["warn"] else 0
                status = "critical"
        else:
            # For wealth: purely trend-based
            if direction == "rising":
                metric_score = 100
                status = "good"
            elif direction == "stable":
                metric_score = 50
                status = "warning"
            else:
                metric_score = 20
                status = "critical"

        total_score += metric_score * info["weight"]
        factors.append({
            "metric": info["name"],
            "direction": direction,
            "status": status,
            "value": round(val, 1),
        })

    score = round(total_score)
    if score >= 75:
        verdict = "improving"
    elif score >= 50:
        verdict = "stable"
    elif score >= 25:
        verdict = "declining"
    else:
        verdict = "critical"

    return {"verdict": verdict, "score": score, "factors": factors}


def _score_game_path_snapshot(current: dict) -> dict:
    """Score game path from a single snapshot (no trend data available)."""
    return _score_game_path(current, {m: 0 for m in FORECAST_METRICS})
