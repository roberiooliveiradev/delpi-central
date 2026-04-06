from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutiveSummaryVariationResponse:
    value: float
    direction: str
    vs_label: str


@dataclass
class ExecutiveSummaryDepartmentResponse:
    id: str
    name: str
    short_name: str
    weight_pct: int
    score: float
    contribution: float
    trend: str
    strategic_summary: str
    key_indicators: list[str]
    executive_goal: str


@dataclass
class ExecutiveSummaryAlertResponse:
    title: str
    severity: str
    impact: str
    recommendation: str


@dataclass
class GetStrategicIndicatorsExecutiveSummaryResponse:
    competence: str
    igd: float
    igd_exact: float
    classification: str
    variation: ExecutiveSummaryVariationResponse
    departments: list[ExecutiveSummaryDepartmentResponse]
    alerts_summary: list[ExecutiveSummaryAlertResponse]