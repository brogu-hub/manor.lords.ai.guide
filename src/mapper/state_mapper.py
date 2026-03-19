"""Map raw uesave JSON to clean GameState.

Manor Lords save structure (uesave format):
  root.properties.savedRegions_0[N] — region data (player region has isSettled_0=True)
  root.properties.savedBuildings_0[] — all buildings with Inventory_0
  root.properties.savedUnits_0[] — all units (Ox, Husband, Wife, Son, etc.)
  root.properties.savedLords_0[] — lord data (treasury, influence)
  root.properties.Year_0, day_0 — time
"""

import logging
from collections import Counter

import math

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
    RealmMap,
    ResourceNode,
    ResourceState,
    SettlementState,
)

logger = logging.getLogger(__name__)

# Manor Lords resource type ID → name mapping
# Discovered from save file analysis
RESOURCE_TYPES = {
    1: "timber",
    3: "stone",
    4: "planks",
    5: "firewood",
    6: "iron_ore",
    7: "iron_slabs",
    8: "clay",
    9: "tiles",
    10: "bread",
    11: "flour",
    12: "grain",  # wheat/emmer
    13: "berries",
    14: "meat",
    15: "hides",
    16: "leather",
    17: "linen",
    18: "yarn",
    23: "ale",
    27: "malt",
    28: "vegetables",
    29: "eggs",
    30: "fish",
    31: "honey",
    32: "charcoal",
    33: "tools",
    34: "shoes",
    35: "cloaks",
    36: "shields",
    37: "swords",
    38: "bows",
    39: "arrows",
    40: "spears",
    41: "polearms",
    42: "helmets",
    43: "armor",
    44: "horses",
    45: "salt",
    46: "dye",
    47: "herbs",
    48: "wax",
    49: "candles",
    50: "apples",
    172: "timber",  # Alternate timber ID seen in saves
    216: "stone",   # Alternate stone ID seen in saves
    234: "ox",      # Livestock
}

# Building type ID → name mapping
BUILDING_TYPES = {
    30: "logging_camp",
    39: "hitching_post",
    85: "burgage_plot",
    87: "well",
    88: "storehouse",
    100: "marketplace",
    115: "road",
}

# Day-to-season mapping (Manor Lords has ~365 days/year)
def _day_to_season(day: int) -> str:
    """Convert day-of-year to season name."""
    if day < 91:
        return "Spring"
    elif day < 182:
        return "Summer"
    elif day < 274:
        return "Autumn"
    else:
        return "Winter"


def _find_player_region(regions: list) -> dict | None:
    """Find the player's settled region."""
    for region in regions:
        if region.get("isSettled_0") and region.get("settlementType_0") == "ESettlementType::Town":
            return region
    # Fallback: first settled region
    for region in regions:
        if region.get("isSettled_0"):
            return region
    return None


def _find_player_lord(lords: list) -> dict | None:
    """Find the player's lord (non-AI, non-bandit)."""
    for lord in lords:
        if not lord.get("isAI_0") and not lord.get("isBandit_0"):
            return lord
    return lords[0] if lords else None


def _aggregate_resources(buildings: list) -> dict[str, float]:
    """Sum up all resources across building inventories."""
    totals: dict[str, float] = {}
    for bld in buildings:
        for item in bld.get("Inventory_0", []):
            if not isinstance(item, dict):
                continue
            type_id = item.get("Type_0", -1)
            amount = item.get("amt_0", 0)
            name = RESOURCE_TYPES.get(type_id, f"unknown_{type_id}")
            totals[name] = totals.get(name, 0) + amount
    return totals


def _count_units(units: list) -> dict:
    """Count units by role."""
    roles = Counter()
    for unit in units:
        if unit.get("dead_0"):
            continue
        role = unit.get("currentUnitRole_0", "Unknown")
        roles[role] += 1
    return dict(roles)


def _count_buildings(buildings: list) -> list[BuildingInfo]:
    """Count buildings by type for the building list."""
    type_counts = Counter()
    type_workers = Counter()
    for bld in buildings:
        bt = bld.get("bType_0", -1)
        name = BUILDING_TYPES.get(bt, f"building_{bt}")
        if name == "road":
            continue  # Skip roads
        type_counts[name] += 1
        type_workers[name] += bld.get("activeWorkers_0", 0)

    return [
        BuildingInfo(
            type=name,
            workers_assigned=type_workers[name],
            level=1,
        )
        for name, count in type_counts.most_common()
    ]


# Resource node type → medieval name
NODE_TYPES = {
    "ENodeType::Iron": "iron deposit",
    "ENodeType::Stone": "stone quarry",
    "ENodeType::Clay": "clay pit",
    "ENodeType::Berries": "berry thicket",
    "ENodeType::SmallGame": "hunting grounds",
    "ENodeType::Fish": "fishing waters",
    "ENodeType::Eel": "eel pond",
    "ENodeType::Salt": "salt spring",
    "ENodeType::Mushrooms": "mushroom grove",
    "ENodeType::BanditCamp": "bandit camp",
}


def _compass_direction(dx: float, dy: float) -> str:
    """Convert delta x/y to a compass direction (medieval style)."""
    angle = math.degrees(math.atan2(dy, dx))
    # UE5 coordinate system: X = east, Y = north (approximately)
    if -22.5 <= angle < 22.5:
        return "east"
    elif 22.5 <= angle < 67.5:
        return "north-east"
    elif 67.5 <= angle < 112.5:
        return "north"
    elif 112.5 <= angle < 157.5:
        return "north-west"
    elif angle >= 157.5 or angle < -157.5:
        return "west"
    elif -157.5 <= angle < -112.5:
        return "south-west"
    elif -112.5 <= angle < -67.5:
        return "south"
    else:
        return "south-east"


def _distance_label(dist: float) -> str:
    """Convert raw distance to a medieval-style proximity label."""
    if dist < 5000:
        return "nearby"
    elif dist < 15000:
        return "a short ride"
    elif dist < 30000:
        return "a fair distance"
    else:
        return "far afield"


def _map_resource_nodes(nodes: list, center_x: float, center_y: float) -> list[ResourceNode]:
    """Extract resource nodes with compass directions relative to settlement center."""
    result = []
    for node in nodes:
        node_type = node.get("nodeType_0", "")
        name = NODE_TYPES.get(node_type)
        if not name:
            continue

        loc = node.get("Location_0", {})
        nx = loc.get("x", 0) if isinstance(loc, dict) else 0
        ny = loc.get("y", 0) if isinstance(loc, dict) else 0

        dx = nx - center_x
        dy = ny - center_y
        dist = math.sqrt(dx * dx + dy * dy)

        result.append(ResourceNode(
            type=name,
            rich=bool(node.get("bRichNode_0")),
            direction=_compass_direction(dx, dy),
            distance=_distance_label(dist),
        ))
    return result


def _build_map_summary(nodes: list[ResourceNode], region_count: int, settled: int) -> str:
    """Build a prose summary of the realm's geography for Gerald."""
    if not nodes:
        return "The land's bounty remains unsurveyed."

    # Group by type
    by_type: dict[str, list[ResourceNode]] = {}
    for n in nodes:
        by_type.setdefault(n.type, []).append(n)

    parts = [f"The realm spans {region_count} territories, {settled} settled."]
    for ntype, group in sorted(by_type.items()):
        rich = [n for n in group if n.rich]
        dirs = list({n.direction for n in group})
        if rich:
            parts.append(f"Rich {ntype} lies to the {dirs[0]}.")
        else:
            dir_str = " and ".join(dirs[:2])
            parts.append(f"{ntype.title()} found to the {dir_str} ({group[0].distance}).")

    return " ".join(parts)


def map_state(raw_json: dict) -> GameState:
    """Map raw uesave JSON properties to a clean GameState object.

    Args:
        raw_json: The properties dict from parse_save() (uesave format).

    Returns:
        GameState with all discovered values populated.
    """
    # Handle both full uesave output and pre-extracted properties
    if "root" in raw_json:
        props = raw_json["root"].get("properties", {})
    elif "properties" in raw_json:
        props = raw_json["properties"]
    else:
        props = raw_json

    # Meta
    year = props.get("Year_0", 0)
    day = props.get("day_0", 0)
    season = _day_to_season(day)

    meta = MetaState(
        year=year,
        season=season,
        day=day,
    )

    # Find player region
    regions = props.get("savedRegions_0", [])
    player_region = _find_player_region(regions)

    if player_region is None:
        logger.warning("No player region found in save")
        return GameState(meta=meta)

    # Population
    families = player_region.get("workerFamilies_0", [])
    units = props.get("savedUnits_0", [])
    unit_counts = _count_units(units)

    population = PopulationState(
        families=len(families),
        workers=unit_counts.get("EUnitRole::Husband", 0),
        homeless=0,  # TODO: detect from burgage vacancy
    )

    # Settlement
    lords = props.get("savedLords_0", [])
    player_lord = _find_player_lord(lords)

    settlement = SettlementState(
        name=player_region.get("CustomName_0", "Unknown"),
        approval=player_region.get("Approval_0", 0),
        population=population,
        regional_wealth=player_region.get("regionalWealth_0", 0),
        lord_personal_wealth=player_lord.get("treasury_0", 0) if player_lord else 0,
    )

    # Resources — aggregate from all building inventories
    buildings = props.get("savedBuildings_0", [])
    resources = _aggregate_resources(buildings)

    food = FoodState(
        total=sum(resources.get(k, 0) for k in [
            "bread", "berries", "meat", "vegetables", "eggs", "fish",
            "honey", "apples", "grain",
        ]),
        bread=resources.get("bread", 0),
        berries=resources.get("berries", 0),
        meat=resources.get("meat", 0),
        vegetables=resources.get("vegetables", 0),
        eggs=resources.get("eggs", 0),
        fish=resources.get("fish", 0),
    )

    fuel = FuelState(
        firewood=resources.get("firewood", 0),
        charcoal=resources.get("charcoal", 0),
    )

    construction = ConstructionState(
        timber=resources.get("timber", 0),
        planks=resources.get("planks", 0),
        stone=resources.get("stone", 0),
        clay=resources.get("clay", 0),
    )

    clothing = ClothingState(
        leather=resources.get("leather", 0),
        linen=resources.get("linen", 0),
        shoes=resources.get("shoes", 0),
        cloaks=resources.get("cloaks", 0),
    )

    production = ProductionState(
        iron=resources.get("iron_slabs", 0),
        ale=resources.get("ale", 0),
        malt=resources.get("malt", 0),
        flour=resources.get("flour", 0),
        yarn=resources.get("yarn", 0),
    )

    resource_state = ResourceState(
        food=food,
        fuel=fuel,
        construction=construction,
        clothing=clothing,
        production=production,
    )

    # Buildings
    building_list = _count_buildings(buildings)

    # Military
    squads = props.get("squads_0", [])
    bandit_camps = sum(
        1 for node in props.get("savedResourceNodes_0", [])
        if node.get("nodeType_0") == "ENodeType::BanditCamp"
    )

    military = MilitaryState(
        retinue_count=0,  # TODO: count from squads
        levies_mobilised=False,
        bandit_camps_nearby=bandit_camps,
    )

    # Development points
    dev_points = player_region.get("devPoints_0", 0)

    # Realm map — resource nodes with compass directions
    center = player_region.get("Center_0", {})
    center_x = center.get("x", 0) if isinstance(center, dict) else 0
    center_y = center.get("y", 0) if isinstance(center, dict) else 0

    raw_nodes = props.get("savedResourceNodes_0", [])
    resource_nodes = _map_resource_nodes(raw_nodes, center_x, center_y)
    settled_count = sum(1 for r in regions if r.get("isSettled_0"))

    realm_map = RealmMap(
        resource_nodes=resource_nodes,
        region_count=len(regions),
        settled_regions=settled_count,
        summary=_build_map_summary(resource_nodes, len(regions), settled_count),
    )

    state = GameState(
        meta=meta,
        settlement=settlement,
        resources=resource_state,
        buildings=building_list,
        military=military,
        realm_map=realm_map,
        development_points=dev_points,
        alerts=[],
    )

    logger.info(
        "Mapped state: Year %d %s, %d families, Approval %.0f, Food %.0f",
        meta.year, meta.season, population.families,
        settlement.approval, food.total,
    )

    return state
