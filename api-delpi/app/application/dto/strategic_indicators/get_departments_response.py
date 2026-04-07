from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DepartmentVariationResponse:
    value: float
    direction: str


@dataclass
class DepartmentListItemResponse:
    id: str
    name: str
    short_name: str
    weight_pct: int
    score: float
    classification: str
    contribution: float
    aggregation_mode: str
    strategic_summary: str
    variation: DepartmentVariationResponse


@dataclass
class GetStrategicIndicatorsDepartmentsResponse:
    items: list[DepartmentListItemResponse]