from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DepartmentDetailsVariationResponse:
    value: float
    direction: str


@dataclass
class DepartmentUnitScoreResponse:
    unit_id: str
    unit_name: str
    score: float
    classification: str


@dataclass
class DepartmentIndicatorDetailsResponse:
    id: str
    name: str
    weight_pct: int
    goal_label: str
    goal_value: float
    goal_periodicity: str
    goal_mode: str = "standard"
    monthly_targets: list[dict] = field(default_factory=list)
    strategic_description: str = ""
    scope_type: str = "consolidated"
    performance_direction: str = "higher_is_better"
    realized: dict = field(default_factory=dict)
    score: float = 0.0
    gap: float = 0.0
    trend: str = "stable"


@dataclass
class GetStrategicIndicatorsDepartmentDetailsResponse:
    id: str
    name: str
    short_name: str
    weight_pct: int
    score: float
    classification: str
    contribution: float
    aggregation_mode: str
    strategic_summary: str
    variation: DepartmentDetailsVariationResponse
    units: list[DepartmentUnitScoreResponse]
    indicators: list[DepartmentIndicatorDetailsResponse]