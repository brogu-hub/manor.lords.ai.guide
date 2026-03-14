"""Pydantic models for Manor Lords game state."""

from pydantic import BaseModel


class MetaState(BaseModel):
    year: int = 0
    season: str = "Unknown"
    day: int = 0
    game_speed: str = "unknown"


class PopulationState(BaseModel):
    families: int = 0
    workers: int = 0
    homeless: int = 0


class SettlementState(BaseModel):
    name: str = "Unknown"
    approval: float = 0.0
    population: PopulationState = PopulationState()
    regional_wealth: float = 0.0
    lord_personal_wealth: float = 0.0


class FoodState(BaseModel):
    total: float = 0.0
    bread: float = 0.0
    berries: float = 0.0
    meat: float = 0.0
    vegetables: float = 0.0
    eggs: float = 0.0
    fish: float = 0.0


class FuelState(BaseModel):
    firewood: float = 0.0
    charcoal: float = 0.0


class ConstructionState(BaseModel):
    timber: float = 0.0
    planks: float = 0.0
    stone: float = 0.0
    clay: float = 0.0


class ClothingState(BaseModel):
    leather: float = 0.0
    linen: float = 0.0
    shoes: float = 0.0
    cloaks: float = 0.0


class ProductionState(BaseModel):
    iron: float = 0.0
    ale: float = 0.0
    malt: float = 0.0
    flour: float = 0.0
    yarn: float = 0.0


class ResourceState(BaseModel):
    food: FoodState = FoodState()
    fuel: FuelState = FuelState()
    construction: ConstructionState = ConstructionState()
    clothing: ClothingState = ClothingState()
    production: ProductionState = ProductionState()


class BuildingInfo(BaseModel):
    type: str = ""
    workers_assigned: int = 0
    max_workers: int = 0
    level: int = 1


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
    development_points: int = 0
    alerts: list[str] = []
