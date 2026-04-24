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
from app.domain.ports.strategic_indicators.resolved_indicators_catalog_repository_port import (
    StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
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
        resolved_indicators_catalog_repository: StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._resolved_indicators_catalog_repository = resolved_indicators_catalog_repository
        self._measurements_port = measurements_port
        self._calculator = calculator

        self._catalog_cache: dict[
            tuple[str | None, str | None, str | None, str | None, str | None],
            StrategicIndicatorsCatalogSnapshot,
        ] = {}
        self._measurements_cache: dict[
            tuple[str, str, str | None, str | None],
            tuple[list[StrategicIndicatorMeasuredValue], list[dict]],
        ] = {}

    def get_catalog_snapshot(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> StrategicIndicatorsCatalogSnapshot:
        cache_key = (competence, start_date, end_date, department_id, branch)
        cached = self._catalog_cache.get(cache_key)
        if cached is not None:
            return cached

        departments_catalog = self._departments_catalog_repository.list_departments_catalog()
        if department_id:
            departments_catalog = [
                item
                for item in departments_catalog
                if item.department_id == department_id
            ]

        indicators_catalog = self._resolved_indicators_catalog_repository.list_resolved_indicators_catalog(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
        )

        goals_by_department: dict[str, str] = {}
        if hasattr(self._departments_catalog_repository, "get_department_goal_summary"):
            goals_by_department = self._departments_catalog_repository.get_department_goal_summary()

        if department_id:
            goals_by_department = {
                key: value
                for key, value in goals_by_department.items()
                if key == department_id
            }

        snapshot = StrategicIndicatorsCatalogSnapshot(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            goals_by_department=goals_by_department,
        )
        self._catalog_cache[cache_key] = snapshot
        return snapshot

    def get_period_snapshot(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> StrategicIndicatorsPeriodSnapshot:
        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        catalog = self.get_catalog_snapshot(
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
            branch=branch,
        )

        measurements, measurement_errors = self._get_measurements(
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            department_id=department_id,
            branch=branch,
        )

        calculated_indicators = self._calculator.calculate_indicators(
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            department_id=department_id,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=catalog.departments_catalog,
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

        for index, department in enumerate(calculated_departments):
            strategic_summary = catalog.goals_by_department.get(
                department.department_id,
                department.strategic_summary,
            )
            if strategic_summary != department.strategic_summary:
                calculated_departments[index] = StrategicDepartmentCalculatedValue(
                    department_id=department.department_id,
                    department_name=department.department_name,
                    short_name=department.short_name,
                    weight_pct=department.weight_pct,
                    strategic_summary=strategic_summary,
                    aggregation_mode=department.aggregation_mode,
                    score=department.score,
                    contribution=department.contribution,
                    classification=department.classification,
                    trend=department.trend,
                    indicators=department.indicators,
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
        branch: str | None = None,
    ) -> StrategicIndicatorsComparativeSnapshot:
        current = self.get_period_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )

        prev = previous_period(current.period)

        previous = self.get_period_snapshot(
            competence=prev.competence,
            start_date=prev.start_date,
            end_date=prev.end_date,
            department_id=department_id,
            branch=branch,
        )

        return StrategicIndicatorsComparativeSnapshot(
            catalog=self.get_catalog_snapshot(
                competence=current.period.competence,
                start_date=current.period.start_date,
                end_date=current.period.end_date,
                department_id=department_id,
                branch=branch,
            ),
            current=current,
            previous=previous,
        )

    def get_series_snapshot(
        self,
        *,
        periods: Iterable[ResolvedPeriod],
        department_id: str | None = None,
        branch: str | None = None,
    ) -> list[StrategicIndicatorsPeriodSnapshot]:
        return [
            self.get_period_snapshot(
                competence=period.competence,
                start_date=period.start_date,
                end_date=period.end_date,
                department_id=department_id,
                branch=branch,
            )
            for period in periods
        ]

    def get_series_snapshot_optimized(
        self,
        *,
        periods: list[ResolvedPeriod],
        department_id: str | None = None,
        branch: str | None = None,
    ) -> list[StrategicIndicatorsPeriodSnapshot]:
        measurements_by_period = self._measurements_port.get_indicator_measurements_series(
            periods=periods,
            department_id=department_id,
            branch=branch,
        )

        snapshots: list[StrategicIndicatorsPeriodSnapshot] = []

        for period in periods:
            catalog = self.get_catalog_snapshot(
                competence=period.competence,
                start_date=period.start_date,
                end_date=period.end_date,
                department_id=department_id,
                branch=branch,
            )

            measurements, measurement_errors = measurements_by_period.get(
                period.competence,
                ([], []),
            )

            calculated_indicators = self._calculator.calculate_indicators(
                indicators_catalog=catalog.indicators_catalog,
                measurements=measurements,
                department_id=department_id,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )

            calculated_departments = self._calculator.calculate_departments(
                departments_catalog=catalog.departments_catalog,
                indicators_catalog=catalog.indicators_catalog,
                measurements=measurements,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )

            for index, department in enumerate(calculated_departments):
                strategic_summary = catalog.goals_by_department.get(
                    department.department_id,
                    department.strategic_summary,
                )
                if strategic_summary != department.strategic_summary:
                    calculated_departments[index] = StrategicDepartmentCalculatedValue(
                        department_id=department.department_id,
                        department_name=department.department_name,
                        short_name=department.short_name,
                        weight_pct=department.weight_pct,
                        strategic_summary=strategic_summary,
                        aggregation_mode=department.aggregation_mode,
                        score=department.score,
                        contribution=department.contribution,
                        classification=department.classification,
                        trend=department.trend,
                        indicators=department.indicators,
                    )

            igd, igd_exact, classification = self._calculator.calculate_igd(
                calculated_departments
            )

            snapshots.append(
                StrategicIndicatorsPeriodSnapshot(
                    period=period,
                    measurements=measurements,
                    measurement_errors=measurement_errors,
                    calculated_indicators=calculated_indicators,
                    calculated_departments=calculated_departments,
                    igd=igd,
                    igd_exact=igd_exact,
                    classification=classification,
                )
            )

        return snapshots

    def _get_measurements(
        self,
        *,
        start_date: str,
        end_date: str,
        competence: str | None,
        department_id: str | None,
        branch: str | None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        key = (start_date, end_date, department_id, branch)

        cached = self._measurements_cache.get(key)
        if cached is not None:
            return cached

        result = self._measurements_port.get_measurements(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            department_id=department_id,
            branch=branch,
        )
        self._measurements_cache[key] = result
        return result