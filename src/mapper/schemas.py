"""Pydantic models for Manor Lords game state."""

from pydantic import BaseModel


class MetaState(BaseModel):
    year: int = 0
    season: str = "Unknown"
    day: int = 0
    game_speed: str = "unknown"
    game_version: str = ""


class PopulationState(BaseModel):
    families: int = 0
    workers: int = 0
    homeless: int = 0


class TaxState(BaseModel):
    land_tax: int = 0
    tithe: int = 0


class SettlementState(BaseModel):
    name: str = "Unknown"
    approval: float = 0.0
    population: PopulationState = PopulationState()
    regional_wealth: float = 0.0
    lord_personal_wealth: float = 0.0
    lord_influence: float = 0.0
    taxes: TaxState = TaxState()


class FoodState(BaseModel):
    total: float = 0.0
    bread: float = 0.0
    berries: float = 0.0
    meat: float = 0.0
    small_game: float = 0.0
    vegetables: float = 0.0
    eggs: float = 0.0
    fish: float = 0.0
    mushrooms: float = 0.0
    herbs: float = 0.0
    grain: float = 0.0
    flour: float = 0.0
    honey: float = 0.0
    apples: float = 0.0


class FuelState(BaseModel):
    firewood: float = 0.0
    charcoal: float = 0.0


class ConstructionState(BaseModel):
    timber: float = 0.0
    planks: float = 0.0
    stone: float = 0.0
    rubblestone: float = 0.0
    clay: float = 0.0
    tools: float = 0.0


class ClothingState(BaseModel):
    hides: float = 0.0
    pelts: float = 0.0
    leather: float = 0.0
    linen: float = 0.0
    yarn: float = 0.0
    shoes: float = 0.0
    cloaks: float = 0.0


class ProductionState(BaseModel):
    iron: float = 0.0
    iron_ore: float = 0.0
    ale: float = 0.0
    malt: float = 0.0
    flour: float = 0.0
    yarn: float = 0.0
    tools: float = 0.0
    tiles: float = 0.0


class MilitaryGoods(BaseModel):
    shields: float = 0.0
    swords: float = 0.0
    bows: float = 0.0
    arrows: float = 0.0
    spears: float = 0.0
    polearms: float = 0.0
    helmets: float = 0.0
    armor: float = 0.0
    horses: float = 0.0


class TradeGoods(BaseModel):
    salt: float = 0.0
    dye: float = 0.0
    herbs: float = 0.0
    wax: float = 0.0
    candles: float = 0.0
    honey: float = 0.0


class ResourceState(BaseModel):
    food: FoodState = FoodState()
    fuel: FuelState = FuelState()
    construction: ConstructionState = ConstructionState()
    clothing: ClothingState = ClothingState()
    production: ProductionState = ProductionState()
    military_goods: MilitaryGoods = MilitaryGoods()
    trade_goods: TradeGoods = TradeGoods()
    other: dict[str, float] = {}  # catch-all for unmapped resources


class BuildingInfo(BaseModel):
    type: str = ""
    count: int = 1
    workers_assigned: int = 0
    max_workers: int = 0
    level: int = 1


class ResourceNode(BaseModel):
    """A natural resource deposit or gathering site on the realm's map."""
    type: str = ""       # e.g. "iron", "berries", "stone", "clay", "fish"
    rich: bool = False   # bountiful deposit
    direction: str = ""  # compass from settlement center
    distance: str = ""   # "near", "mid", "far"


class RealmMap(BaseModel):
    """Spatial overview of the lord's territory."""
    resource_nodes: list[ResourceNode] = []
    region_count: int = 0
    settled_regions: int = 0
    summary: str = ""    # human-readable spatial summary for Gerald


class MilitaryState(BaseModel):
    retinue_count: int = 0
    retinue_equipment: str = "none"
    levies_mobilised: bool = False
    bandit_camps_nearby: int = 0
    active_raid: bool = False


class GameState(BaseModel):
    """Complete Manor Lords game state extracted from a save file."""
    meta: MetaState = MetaState()
    settlement: SettlementState = SettlementState()
    resources: ResourceState = ResourceState()
    buildings: list[BuildingInfo] = []
    military: MilitaryState = MilitaryState()
    realm_map: RealmMap = RealmMap()
    development_points: int = 0
    alerts: list[str] = []
