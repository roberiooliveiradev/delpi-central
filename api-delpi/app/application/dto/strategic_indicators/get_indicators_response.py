from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IndicatorItemResponse:
    department_id: str
    department_name: str
    indicator_id: str
    indicator_name: str
    weight_pct: int
    goal_2026: str
    scope_type: str
    value: float
    score: float
    gap: float
    trend: str
    classification: str
    source: str


@dataclass
class GetStrategicIndicatorsResponse:
    items: list[IndicatorItemResponse]