from __future__ import annotations

from dataclasses import dataclass


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
    goal_2026: str
    strategic_description: str
    scope_type: str
    realized: dict
    score: float
    gap: float
    trend: str


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