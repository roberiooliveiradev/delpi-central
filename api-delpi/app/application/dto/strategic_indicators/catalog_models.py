from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrategicIndicatorCatalogItem:
    indicator_id: str
    department_id: str
    indicator_name: str
    weight_pct: float
    goal_label: str
    goal_value: float
    goal_periodicity: str
    goal_mode: str = "standard"
    monthly_targets: list[dict] = field(default_factory=list)
    scope_type: str = "consolidated"
    performance_direction: str = "higher_is_better"
    strategic_description: str = ""
    source_key: str | None = None


@dataclass(frozen=True)
class StrategicDepartmentCatalogItem:
    department_id: str
    department_name: str
    short_name: str
    weight_pct: float
    strategic_summary: str
    aggregation_mode: str


@dataclass(frozen=True)
class StrategicIndicatorMeasuredValue:
    indicator_id: str
    department_id: str
    value: float
    source: str
    unit_values: dict[str, float] | None = None


@dataclass(frozen=True)
class StrategicIndicatorCalculatedValue:
    indicator_id: str
    department_id: str
    indicator_name: str
    weight_pct: float
    goal_label: str
    goal_value: float
    goal_periodicity: str
    goal_mode: str = "standard"
    monthly_targets: list[dict] = field(default_factory=list)
    scope_type: str = "consolidated"
    performance_direction: str = "higher_is_better"
    strategic_description: str = ""
    source: str = ""
    value: float = 0.0
    score: float = 0.0
    gap: float = 0.0
    trend: str = "stable"
    classification: str = ""
    unit_values: dict[str, float] | None = None


@dataclass(frozen=True)
class StrategicDepartmentCalculatedValue:
    department_id: str
    department_name: str
    short_name: str
    weight_pct: float
    strategic_summary: str
    aggregation_mode: str
    score: float
    contribution: float
    classification: str
    trend: str
    indicators: list[StrategicIndicatorCalculatedValue]