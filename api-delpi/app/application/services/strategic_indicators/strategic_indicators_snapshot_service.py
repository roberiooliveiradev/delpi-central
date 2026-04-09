from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    previous_period,
    resolve_period,
)
from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from app.domain.ports.strategic_indicators.departments_catalog_repository_port import (
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
)
from app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from app.domain.ports.strategic_indicators.indicators_catalog_repository_port import (
    StrategicIndicatorsIndicatorsCatalogRepositoryPort,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
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
class StrategicIndicatorsComparativeSnapshot:
    catalog: StrategicIndicatorsCatalogSnapshot
    current: StrategicIndicatorsPeriodSnapshot
    previous: StrategicIndicatorsPeriodSnapshot


class StrategicIndicatorsSnapshotService:
    def __init__(
        self,
        *,
        departments_catalog_repository: StrategicIndicatorsDepartmentsCatalogRepositoryPort,
        indicators_catalog_repository: StrategicIndicatorsIndicatorsCatalogRepositoryPort,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._indicators_catalog_repository = indicators_catalog_repository
        self._measurements_port = measurements_port
        self._calculator = calculator

        self._catalog_cache: StrategicIndicatorsCatalogSnapshot | None = None
        self._measurements_cache: dict[
            tuple[str, str, str | None],
            tuple[list[StrategicIndicatorMeasuredValue], list[dict]],
        ] = {}

    def get_catalog_snapshot(self) -> StrategicIndicatorsCatalogSnapshot:
        if self._catalog_cache is not None:
            return self._catalog_cache

        departments_catalog = self._departments_catalog_repository.list_departments_catalog()
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        goals_by_department: dict[str, str] = {}
        if hasattr(self._departments_catalog_repository, "get_department_goal_summary"):
            goals_by_department = self._departments_catalog_repository.get_department_goal_summary()

        self._catalog_cache = StrategicIndicatorsCatalogSnapshot(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            goals_by_department=goals_by_department,
        )
        return self._catalog_cache

    def get_period_snapshot(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> StrategicIndicatorsPeriodSnapshot:
        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        catalog = self.get_catalog_snapshot()

        measurements, measurement_errors = self._get_measurements(
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
        )

        departments_catalog = catalog.departments_catalog
        if department_id:
            departments_catalog = [
                item
                for item in catalog.departments_catalog
                if item.department_id == department_id
            ]

        calculated_indicators = self._calculator.calculate_indicators(
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            department_id=department_id,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

        igd, igd_exact, classification = self._calculator.calculate_igd(
            calculated_departments
        )

        return StrategicIndicatorsPeriodSnapshot(
            period=period,
            measurements=measurements,
            measurement_errors=measurement_errors,
            calculated_indicators=calculated_indicators,
            calculated_departments=calculated_departments,
            igd=igd,
            igd_exact=igd_exact,
            classification=classification,
        )

    def get_current_and_previous_snapshot(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> StrategicIndicatorsComparativeSnapshot:
        current = self.get_period_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
        )

        prev = previous_period(current.period)

        previous = self.get_period_snapshot(
            competence=prev.competence,
            start_date=prev.start_date,
            end_date=prev.end_date,
            department_id=department_id,
        )

        return StrategicIndicatorsComparativeSnapshot(
            catalog=self.get_catalog_snapshot(),
            current=current,
            previous=previous,
        )

    def get_series_snapshot(
        self,
        *,
        periods: Iterable[ResolvedPeriod],
        department_id: str | None = None,
    ) -> list[StrategicIndicatorsPeriodSnapshot]:
        return [
            self.get_period_snapshot(
                competence=period.competence,
                start_date=period.start_date,
                end_date=period.end_date,
                department_id=department_id,
            )
            for period in periods
        ]

    def _get_measurements(
        self,
        *,
        start_date: str,
        end_date: str,
        department_id: str | None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        key = (start_date, end_date, department_id)

        cached = self._measurements_cache.get(key)
        if cached is not None:
            return cached

        result = self._measurements_port.get_indicator_measurements(
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
        )
        self._measurements_cache[key] = result
        return result