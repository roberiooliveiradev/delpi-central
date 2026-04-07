from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategicIndicatorCatalogItem:
    indicator_id: str
    department_id: str
    indicator_name: str
    weight_pct: float
    goal_2026: str
    scope_type: str
    strategic_description: str
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
    goal_2026: str
    scope_type: str
    strategic_description: str
    source: str
    value: float
    score: float
    gap: float
    trend: str
    classification: str
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