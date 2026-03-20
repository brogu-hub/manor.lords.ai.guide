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
    MilitaryGoods,
    MilitaryState,
    PopulationState,
    ProductionState,
    RealmMap,
    ResourceNode,
    ResourceState,
    SettlementState,
    TaxState,
    TradeGoods,
)

logger = logging.getLogger(__name__)

# Manor Lords resource type ID → name mapping
# Based on official resource flowchart + save file analysis
RESOURCE_TYPES = {
    # === CONFIRMED by user (v0.8.065) ===
    6: "tools",          # 8 matched exactly
    9: "pelts",          # hunter's camp bi-product
    15: "rubblestone",   # 10 matched exactly
    16: "timber",        # sawpit produces this
    17: "planks",        # 94 matched exactly
    18: "herbs",         # forager hut produces alongside mushrooms
    216: "firewood",     # woodcutter produces
    279: "mushrooms",    # forager hut
    330: "small_game",   # hunter's camp bi-product
    146: "clay",          # confirmed v0.8.065
    # === From resource flowchart (not yet confirmed in v0.8.065) ===
    # Timber & fuel
    1: "timber",
    4: "planks",
    5: "firewood",
    32: "charcoal",
    172: "timber",
    # Stone & construction
    3: "stone",
    8: "clay",
    257: "rubblestone",
    # Food
    10: "bread",
    11: "flour",
    12: "grain",
    13: "charcoal",      # confirmed v0.8.065 (was berries in old versions)
    14: "meat",
    28: "vegetables",
    29: "eggs",
    30: "fish",
    31: "honey",
    47: "herbs",
    50: "apples",
    # Animal products (IDs may differ in v0.8.065)
    # Clothing & textiles
    34: "shoes",
    35: "cloaks",
    # Industry
    7: "iron_slabs",
    33: "tools",
    # Alcohol
    23: "ale",
    27: "malt",
    # Military
    36: "shields",
    37: "swords",
    38: "bows",
    39: "arrows",
    40: "spears",
    41: "polearms",
    42: "helmets",
    43: "armor",
    # Trade & luxury
    44: "horses",
    45: "salt",
    46: "dye",
    48: "wax",
    49: "candles",
    # Livestock
    234: "ox",
}

# Building type ID → name mapping (confirmed by user for v0.8.065)
BUILDING_TYPES = {
    3: "burgage_plot",        # residential (occupants, refuel, variety)
    6: "trading_post",
    7: "foresters_hut",      # plants trees, produces saplings
    8: "burgage_plot",       # residential with extensions (chicken coop etc)
    10: "pack_station",      # hp=0, no workers — logistics
    13: "well",
    18: "marketplace",
    20: "communal_oven",     # hp=300, no workers — passive food processing
    21: "stone_gatherer_camp",
    26: "livestock_trading_post",  # refuel=True, no occupants
    30: "logging_camp",
    34: "church",
    37: "sheep_pasture",     # hp=260, 1 worker — livestock grazing
    42: "hitching_post",
    59: "fishermans_hut",
    68: "granary",
    69: "farmhouse",         # confirmed: 4+3 workers on 2 farmhouses
    72: "storehouse",
    97: "sawpit",            # hp=55, produces planks
    79: "field",             # hp=55, 1 worker — farmhouse field
    112: "corpse_pit",       # hp=5 — sanitation
    113: "pasture_fence",    # hp=0 — field boundary
    115: "road",
}

# cropType enum → building name (from resource flowchart)
_CROP_BUILDING = {
    "ECropType::AnimalTraps": "hunters_camp",
    "ECropType::Wheat": "farmhouse",
    "ECropType::Rye": "farmhouse",
    "ECropType::Barley": "farmhouse",
    "ECropType::Flax": "farmhouse",
    "ECropType::Vegetables": "vegetable_garden",
    "ECropType::Berries": "forager_hut",
    "ECropType::Herbs": "forager_hut",
    "ECropType::Mushrooms": "forager_hut",
    "ECropType::Apples": "orchard",
    "ECropType::Honey": "apiary",
    "ECropType::Fish": "fishermans_hut",
    "ECropType::Sheep": "sheep_farm",
    "ECropType::Chickens": "chicken_coop",
}


def _identify_building(bld: dict) -> str:
    """Identify a building from its save data properties.

    Uses behavioral heuristics rather than hardcoded type IDs,
    since IDs change between game versions.
    """
    bt = bld.get("bType_0", -1)

    if bt in BUILDING_TYPES:
        return BUILDING_TYPES[bt]

    # Not yet constructed (planned/ghost)
    if not bld.get("wasFullyConstructed_0", False) and bld.get("localHp_0", 0) < 1:
        return "construction_site"

    # Production: identified by crop type (check BEFORE residential)
    crop = bld.get("cropType_0", "")
    if crop in _CROP_BUILDING:
        return _CROP_BUILDING[crop]

    # Forager / gatherer: has work area + protect resource area + no crop
    if (bld.get("bProtectResourceArea_0", False)
        and crop not in _CROP_BUILDING
        and not bld.get("occupantFamilyIDs_0")):
        prod_types_check = {p.get("ItemType_0") for p in bld.get("productionLogMap_0", [])}
        # Forager outputs: berries(13), mushrooms(279), herbs(18/47)
        if prod_types_check.intersection({13, 18, 47, 279}):
            return "forager_hut"

    # Production: identified by what it produces (based on resource flowchart)
    prod_types = {p.get("ItemType_0") for p in bld.get("productionLogMap_0", [])}
    if prod_types:
        # Timber & fuel chain
        if 216 in prod_types or 5 in prod_types:
            return "woodcutter_lodge"
        if 16 in prod_types:
            return "logging_camp"  # produces timber(16)
        if 32 in prod_types:
            return "charcoal_kiln"
        # Stone chain
        if 257 in prod_types or 3 in prod_types:
            return "stone_gatherer_camp"
        if 15 in prod_types:
            return "stonemason"  # produces rubblestone(15)
        # Mining & metal
        if 7 in prod_types:
            return "bloomery"
        if 6 in prod_types or 33 in prod_types:
            return "smithy"  # produces tools(6)
        # Food processing
        if 11 in prod_types:
            return "windmill"
        if 10 in prod_types:
            return "bakery"
        if 27 in prod_types:
            return "malthouse"
        if 23 in prod_types:
            return "brewery"
        # Clothing
        if 17 in prod_types and not prod_types.intersection({279, 13}):
            return "weaver_workshop"  # produces linen(17) but not forager
        if 34 in prod_types:
            return "cobbler_workshop"
        if 35 in prod_types:
            return "tailor_workshop"
        # Military
        if {36, 37, 40, 41}.intersection(prod_types):
            return "blacksmith_workshop"
        if {38}.intersection(prod_types):
            return "bowyer_workshop"
        if {42, 43}.intersection(prod_types):
            return "armory"

    # Residential: MUST have actual occupants or houseVariety > 0 (actual house, not empty field)
    occupants = bld.get("occupantFamilyIDs_0")
    has_occupants = occupants is not None and len(occupants) > 0
    is_house = bld.get("houseVariety_0", -1) > 0
    if has_occupants and is_house:
        return "burgage_plot"

    # Storage: has inventory but no production, no occupants living in it
    inv = bld.get("Inventory_0", [])
    has_items = any(isinstance(i, dict) and i.get("amt_0", 0) > 0 for i in inv)
    if has_items and not prod_types and not has_occupants:
        # Storehouses have assigned families or high HP; ground stockpiles are simpler
        assigned = bld.get("assignedFamilyIDs_0", [])
        hp = bld.get("localHp_0", 0)
        if (assigned and len(assigned) > 0) or hp >= 50:
            return "storehouse"
        return "stockpile"

    # Shelter: has occupants but not a proper house
    if has_occupants and not is_house:
        return "shelter"

    # Fallback
    return f"building_{bt}"

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


# Ground resource type → resource name
_GROUND_RESOURCE_MAP = {
    "res_tree": "timber",
    "res_plank": "planks",
    "res_stone": "stone",
    "res_firewood": "firewood",
}


def _count_ground_resources(saved_resources: list) -> dict[str, float]:
    """Count loose resources on the ground (felled trees, dropped goods)."""
    totals: dict[str, float] = {}
    for res in saved_resources:
        res_type = res.get("resType_0", "")
        name = _GROUND_RESOURCE_MAP.get(res_type)
        if name:
            totals[name] = totals.get(name, 0) + 1
    return totals


def _aggregate_resources(buildings: list, ground_resources: list | None = None) -> dict[str, float]:
    """Sum up all resources across building inventories and ground."""
    totals: dict[str, float] = {}

    # Ground resources (felled trees etc)
    if ground_resources:
        for name, count in _count_ground_resources(ground_resources).items():
            totals[name] = totals.get(name, 0) + count

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
    """List buildings with worker assignments.

    Buildings with workers are listed individually so the AI sees
    exact allocation per building (e.g. farmhouse #1: 4, farmhouse #2: 3).
    Empty buildings are grouped by type with a count.
    """
    individual: list[BuildingInfo] = []
    empty_counts: Counter = Counter()

    for bld in buildings:
        name = _identify_building(bld)
        if name in ("road", "construction_site"):
            continue
        workers = bld.get("activeWorkers_0", 0)
        assigned = bld.get("assignedFamilyIDs_0", [])
        num_assigned = len(assigned) if assigned else workers

        if num_assigned > 0:
            individual.append(BuildingInfo(
                type=name,
                count=1,
                workers_assigned=num_assigned,
                level=1,
            ))
        else:
            empty_counts[name] += 1

    # Add grouped empty buildings
    grouped = [
        BuildingInfo(type=name, count=count, workers_assigned=0, level=1)
        for name, count in empty_counts.most_common()
    ]

    return individual + grouped


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

    game_version = props.get("Version_0", "")

    meta = MetaState(
        year=year,
        season=season,
        day=day,
        game_version=game_version,
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

    # Tax rates
    tax_rates = player_region.get("taxRates_0", [])
    tax_map = {t.get("key", ""): t.get("value", 0) for t in tax_rates if isinstance(t, dict)}

    settlement = SettlementState(
        name=player_region.get("CustomName_0", "Unknown"),
        approval=player_region.get("Approval_0", 0),
        population=population,
        regional_wealth=player_region.get("regionalWealth_0", 0),
        lord_personal_wealth=player_lord.get("treasury_0", 0) if player_lord else 0,
        lord_influence=player_lord.get("influence_0", 0) if player_lord else 0,
        taxes=TaxState(
            land_tax=tax_map.get("land", 0),
            tithe=tax_map.get("tithe", 0),
        ),
    )

    # Resources — aggregate from all building inventories
    buildings = props.get("savedBuildings_0", [])
    ground_resources = props.get("savedResources_0", [])
    resources = _aggregate_resources(buildings, ground_resources)

    # Categorise all resources
    _FOOD_KEYS = {"bread", "berries", "meat", "small_game", "vegetables", "eggs", "fish", "honey", "apples", "grain", "flour", "mushrooms", "herbs"}
    _FUEL_KEYS = {"firewood", "charcoal"}
    _CONSTRUCTION_KEYS = {"timber", "planks", "stone", "rubblestone", "clay", "tools"}
    _CLOTHING_KEYS = {"leather", "linen", "shoes", "cloaks", "hides", "pelts", "yarn"}
    _PRODUCTION_KEYS = {"iron_slabs", "iron_ore", "ale", "malt", "tools"}
    _MILITARY_KEYS = {"shields", "swords", "bows", "arrows", "spears", "polearms", "helmets", "armor", "horses"}
    _TRADE_KEYS = {"salt", "dye", "herbs", "wax", "candles"}
    _SKIP_KEYS = {"ox"}
    _ALL_KNOWN = _FOOD_KEYS | _FUEL_KEYS | _CONSTRUCTION_KEYS | _CLOTHING_KEYS | _PRODUCTION_KEYS | _MILITARY_KEYS | _TRADE_KEYS | _SKIP_KEYS

    food = FoodState(
        total=sum(resources.get(k, 0) for k in _FOOD_KEYS),
        bread=resources.get("bread", 0),
        berries=resources.get("berries", 0),
        meat=resources.get("meat", 0),
        small_game=resources.get("small_game", 0),
        vegetables=resources.get("vegetables", 0),
        eggs=resources.get("eggs", 0),
        fish=resources.get("fish", 0),
        mushrooms=resources.get("mushrooms", 0),
        herbs=resources.get("herbs", 0),
        grain=resources.get("grain", 0),
        flour=resources.get("flour", 0),
        honey=resources.get("honey", 0),
        apples=resources.get("apples", 0),
    )

    fuel = FuelState(
        firewood=resources.get("firewood", 0),
        charcoal=resources.get("charcoal", 0),
    )

    construction = ConstructionState(
        timber=resources.get("timber", 0),
        planks=resources.get("planks", 0),
        stone=resources.get("stone", 0),
        rubblestone=resources.get("rubblestone", 0),
        clay=resources.get("clay", 0),
        tools=resources.get("tools", 0),
    )

    clothing = ClothingState(
        hides=resources.get("hides", 0),
        pelts=resources.get("pelts", 0),
        leather=resources.get("leather", 0),
        linen=resources.get("linen", 0),
        yarn=resources.get("yarn", 0),
        shoes=resources.get("shoes", 0),
        cloaks=resources.get("cloaks", 0),
    )

    production = ProductionState(
        iron=resources.get("iron_slabs", 0),
        iron_ore=resources.get("iron_ore", 0),
        ale=resources.get("ale", 0),
        malt=resources.get("malt", 0),
        flour=resources.get("flour", 0),
        yarn=resources.get("yarn", 0),
        tools=resources.get("tools", 0),
        tiles=resources.get("tiles", 0),
    )

    military_goods = MilitaryGoods(
        shields=resources.get("shields", 0),
        swords=resources.get("swords", 0),
        bows=resources.get("bows", 0),
        arrows=resources.get("arrows", 0),
        spears=resources.get("spears", 0),
        polearms=resources.get("polearms", 0),
        helmets=resources.get("helmets", 0),
        armor=resources.get("armor", 0),
        horses=resources.get("horses", 0),
    )

    trade_goods = TradeGoods(
        salt=resources.get("salt", 0),
        dye=resources.get("dye", 0),
        herbs=resources.get("herbs", 0),
        wax=resources.get("wax", 0),
        candles=resources.get("candles", 0),
        honey=resources.get("honey", 0),
    )

    # Catch-all: any resource not in a known category
    other_resources = {
        k: v for k, v in resources.items()
        if k not in _ALL_KNOWN and v > 0
    }

    resource_state = ResourceState(
        food=food,
        fuel=fuel,
        construction=construction,
        clothing=clothing,
        production=production,
        military_goods=military_goods,
        trade_goods=trade_goods,
        other=other_resources,
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
