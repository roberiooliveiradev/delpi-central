from __future__ import annotations

from dataclasses import dataclass

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)


@dataclass(frozen=True)
class StrategicIndicatorsCatalogSnapshot:
    departments_catalog: list[StrategicDepartmentCatalogItem]
    indicators_catalog: list[StrategicIndicatorCatalogItem]
    goals_by_department: dict[str, str]


@dataclass(frozen=True)
class StrategicIndicatorsPeriodSnapshot:
    period: ResolvedPeriod
    measurements: list[StrategicIndicatorMeasuredValue]
    measurement_errors: list[dict]
    calculated_indicators: list[StrategicIndicatorCalculatedValue]
    calculated_departments: list[StrategicDepartmentCalculatedValue]
    igd: float
    igd_exact: float
    classification: str


@dataclass(frozen=True)
class PeriodScoresCacheEntry:
    snapshot: StrategicIndicatorsPeriodSnapshot
    catalog_inputs_hash: str | None = None
    version_number: int = 1
    is_clean: bool = True


@dataclass(frozen=True)
class StrategicIndicatorsComparativeSnapshot:
    catalog: StrategicIndicatorsCatalogSnapshot
    current: StrategicIndicatorsPeriodSnapshot
    previous: StrategicIndicatorsPeriodSnapshot
