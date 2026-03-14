"""Map raw GVAS JSON property tree to clean GameState using YAML config."""

import logging
from pathlib import Path

import yaml

from src.mapper.schemas import (
    BuildingInfo,
    ClothingState,
    ConstructionState,
    FoodState,
    FuelState,
    GameState,
    MetaState,
    MilitaryState,
    PopulationState,
    ProductionState,
    ResourceState,
    SettlementState,
)

logger = logging.getLogger(__name__)


def load_mapper_config(config_path: str | Path | None = None) -> dict:
    """Load the GVAS-to-GameState mapper YAML config."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "manor_lords_mapper.yaml"
    config_path = Path(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_nested_value(data: dict, path: str, default=None):
    """Traverse a nested dict/list using a dot-separated path.

    Supports:
        - Dot notation: 'a.b.c'
        - Array indices: 'a.b[0].c'
    """
    keys = []
    for part in path.split("."):
        if "[" in part:
            key, idx = part.split("[")
            keys.append(key)
            keys.append(int(idx.rstrip("]")))
        else:
            keys.append(part)

    current = data
    for key in keys:
        try:
            if isinstance(key, int):
                current = current[key]
            elif isinstance(current, dict):
                current = current[key]
            else:
                return default
        except (KeyError, IndexError, TypeError):
            return default
    return current


def map_state(raw_json: list | dict, config: dict | None = None) -> GameState:
    """Map raw GVAS JSON to a clean GameState object.

    Args:
        raw_json: The raw property tree from SavConverter (list or dict).
            If a list (SavConverter format), it's first converted to a nested dict
            using properties_to_dict.
        config: Mapper config dict. Loads default if None.

    Returns:
        GameState with all discovered values populated.
    """
    if config is None:
        config = load_mapper_config()

    # Convert SavConverter list format to nested dict for easy traversal
    if isinstance(raw_json, list):
        from src.parser.gvas_parser import properties_to_dict
        raw_json = properties_to_dict(raw_json)

    def get(section: str, field: str, default=None):
        path = config.get(section, {}).get(field, "")
        if not path:
            return default
        return get_nested_value(raw_json, path, default)

    # Map season enum to string
    season_raw = get("meta", "season", 0)
    season_map = config.get("season_map", {})
    if isinstance(season_raw, (int, float)):
        season = season_map.get(int(season_raw), f"Unknown({season_raw})")
    else:
        season = str(season_raw)

    # Build the GameState
    meta = MetaState(
        year=int(get("meta", "year", 0) or 0),
        season=season,
        day=int(get("meta", "day", 0) or 0),
        game_speed=str(get("meta", "game_speed", "unknown") or "unknown"),
    )

    population = PopulationState(
        families=int(get("settlement", "population_families", 0) or 0),
        workers=int(get("settlement", "population_workers", 0) or 0),
        homeless=int(get("settlement", "population_homeless", 0) or 0),
    )

    settlement = SettlementState(
        name=str(get("settlement", "name", "Unknown") or "Unknown"),
        approval=float(get("settlement", "approval", 0) or 0),
        population=population,
        regional_wealth=float(get("settlement", "regional_wealth", 0) or 0),
        lord_personal_wealth=float(get("settlement", "lord_personal_wealth", 0) or 0),
    )

    food = FoodState(
        total=float(get("resources", "food_total", 0) or 0),
        bread=float(get("resources", "food_bread", 0) or 0),
        berries=float(get("resources", "food_berries", 0) or 0),
        meat=float(get("resources", "food_meat", 0) or 0),
        vegetables=float(get("resources", "food_vegetables", 0) or 0),
        eggs=float(get("resources", "food_eggs", 0) or 0),
        fish=float(get("resources", "food_fish", 0) or 0),
    )

    fuel = FuelState(
        firewood=float(get("resources", "firewood", 0) or 0),
        charcoal=float(get("resources", "charcoal", 0) or 0),
    )

    construction = ConstructionState(
        timber=float(get("resources", "timber", 0) or 0),
        planks=float(get("resources", "planks", 0) or 0),
        stone=float(get("resources", "stone", 0) or 0),
        clay=float(get("resources", "clay", 0) or 0),
    )

    clothing = ClothingState(
        leather=float(get("resources", "leather", 0) or 0),
        linen=float(get("resources", "linen", 0) or 0),
    )

    production = ProductionState(
        iron=float(get("resources", "iron", 0) or 0),
        ale=float(get("resources", "ale", 0) or 0),
        malt=float(get("resources", "malt", 0) or 0),
        flour=float(get("resources", "flour", 0) or 0),
        yarn=float(get("resources", "yarn", 0) or 0),
    )

    resources = ResourceState(
        food=food,
        fuel=fuel,
        construction=construction,
        clothing=clothing,
        production=production,
    )

    military = MilitaryState(
        retinue_count=int(get("military", "retinue_count", 0) or 0),
        levies_mobilised=bool(get("military", "levies_mobilised", False)),
        bandit_camps_nearby=int(get("military", "bandit_camps_nearby", 0) or 0),
    )

    dev_points = int(get("development_points", "", 0) or 0)
    # Try top-level path directly for dev points
    if dev_points == 0:
        dp_path = config.get("development_points", "")
        if isinstance(dp_path, str) and dp_path:
            dp_val = get_nested_value(raw_json, dp_path, 0)
            dev_points = int(dp_val or 0)

    return GameState(
        meta=meta,
        settlement=settlement,
        resources=resources,
        buildings=[],  # Buildings require array iteration — populated after path discovery
        military=military,
        development_points=dev_points,
        alerts=[],  # Populated by alert engine
    )
