from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable

from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    previous_period,
    resolve_period,
)
from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.ports.strategic_indicators.departments_catalog_repository_port import (
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
)
from si_app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from si_app.domain.ports.strategic_indicators.resolved_indicators_catalog_repository_port import (
    StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    _catalog_cache as shared_catalog_cache,
    _measurements_cache as shared_measurements_cache,
    catalog_cache_key,
    measurements_cache_key,
)

logger = logging.getLogger("strategic_indicators.snapshot")


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
        measurements_port_factory: Callable[
            [], StrategicIndicatorsIndicatorMeasurementsPort
        ]
        | None = None,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._resolved_indicators_catalog_repository = resolved_indicators_catalog_repository
        self._measurements_port = measurements_port
        self._measurements_port_factory = measurements_port_factory
        self._calculator = calculator

        self._catalog_cache: dict[str, StrategicIndicatorsCatalogSnapshot] = {}
        self._measurements_cache: dict[
            str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]
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
        cache_key = catalog_cache_key(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )
        cached = self._catalog_cache.get(cache_key)
        if cached is not None:
            logger.debug(
                "si_catalog_cache_hit scope=request competence=%s department_id=%s",
                competence,
                department_id,
            )
            return cached

        cached = shared_catalog_cache.get(cache_key)
        if cached is not None:
            self._catalog_cache[cache_key] = cached
            logger.debug(
                "si_catalog_cache_hit scope=shared competence=%s department_id=%s",
                competence,
                department_id,
            )
            return cached

        catalog_started = time.perf_counter()
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
        shared_catalog_cache.set(cache_key, snapshot)
        logger.info(
            (
                "si_catalog_loaded competence=%s department_id=%s "
                "indicators=%d departments=%d ms=%.0f"
            ),
            competence,
            department_id,
            len(indicators_catalog),
            len(departments_catalog),
            (time.perf_counter() - catalog_started) * 1000,
        )
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
        started = time.perf_counter()
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

        snapshot = self._build_period_snapshot(
            period=period,
            catalog=catalog,
            measurements=measurements,
            measurement_errors=measurement_errors,
            department_id=department_id,
        )
        logger.info(
            "si_snapshot period=%s department_id=%s branch=%s total_ms=%.0f",
            period.competence,
            department_id,
            branch,
            (time.perf_counter() - started) * 1000,
        )
        return snapshot

    def get_current_and_previous_snapshot(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> StrategicIndicatorsComparativeSnapshot:
        started = time.perf_counter()
        current_period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        previous_period_resolved = previous_period(current_period)

        measurements_started = time.perf_counter()
        if self._measurements_port_factory is not None:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_current = executor.submit(
                    self._get_measurements,
                    start_date=current_period.start_date,
                    end_date=current_period.end_date,
                    competence=current_period.competence,
                    department_id=department_id,
                    branch=branch,
                    measurements_port=self._measurements_port_factory(),
                )
                future_previous = executor.submit(
                    self._get_measurements,
                    start_date=previous_period_resolved.start_date,
                    end_date=previous_period_resolved.end_date,
                    competence=previous_period_resolved.competence,
                    department_id=department_id,
                    branch=branch,
                    measurements_port=self._measurements_port_factory(),
                )
                measurements_current, errors_current = future_current.result()
                measurements_previous, errors_previous = future_previous.result()
        else:
            measurements_current, errors_current = self._get_measurements(
                start_date=current_period.start_date,
                end_date=current_period.end_date,
                competence=current_period.competence,
                department_id=department_id,
                branch=branch,
            )
            measurements_previous, errors_previous = self._get_measurements(
                start_date=previous_period_resolved.start_date,
                end_date=previous_period_resolved.end_date,
                competence=previous_period_resolved.competence,
                department_id=department_id,
                branch=branch,
            )
        measurements_parallel_ms = (time.perf_counter() - measurements_started) * 1000

        catalog_started = time.perf_counter()
        catalog_current = self.get_catalog_snapshot(
            competence=current_period.competence,
            start_date=current_period.start_date,
            end_date=current_period.end_date,
            department_id=department_id,
            branch=branch,
        )
        catalog_previous = self.get_catalog_snapshot(
            competence=previous_period_resolved.competence,
            start_date=previous_period_resolved.start_date,
            end_date=previous_period_resolved.end_date,
            department_id=department_id,
            branch=branch,
        )
        catalog_ms = (time.perf_counter() - catalog_started) * 1000

        build_started = time.perf_counter()
        current = self._build_period_snapshot(
            period=current_period,
            catalog=catalog_current,
            measurements=measurements_current,
            measurement_errors=errors_current,
            department_id=department_id,
        )
        previous = self._build_period_snapshot(
            period=previous_period_resolved,
            catalog=catalog_previous,
            measurements=measurements_previous,
            measurement_errors=errors_previous,
            department_id=department_id,
        )
        build_ms = (time.perf_counter() - build_started) * 1000
        total_ms = (time.perf_counter() - started) * 1000

        logger.info(
            (
                "si_snapshot_comparative current=%s previous=%s department_id=%s "
                "branch=%s measurements_ms=%.0f catalog_ms=%.0f "
                "build_ms=%.0f total_ms=%.0f "
                "measurements_current=%d measurements_previous=%d "
                "errors_current=%d errors_previous=%d"
            ),
            current_period.competence,
            previous_period_resolved.competence,
            department_id,
            branch,
            measurements_parallel_ms,
            catalog_ms,
            build_ms,
            total_ms,
            len(measurements_current),
            len(measurements_previous),
            len(errors_current),
            len(errors_previous),
        )

        return StrategicIndicatorsComparativeSnapshot(
            catalog=catalog_current,
            current=current,
            previous=previous,
        )

    def _build_period_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        catalog: StrategicIndicatorsCatalogSnapshot,
        measurements: list[StrategicIndicatorMeasuredValue],
        measurement_errors: list[dict],
        department_id: str | None,
    ) -> StrategicIndicatorsPeriodSnapshot:
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
        started = time.perf_counter()
        measurements_started = time.perf_counter()
        if (
            self._measurements_port_factory is not None
            and len(periods) > 1
            and department_id in (None, "")
        ):
            measurements_by_period = self._load_measurements_by_period_parallel(
                periods=periods,
                department_id=department_id,
                branch=branch,
            )
        else:
            measurements_by_period = self._measurements_port.get_indicator_measurements_series(
                periods=periods,
                department_id=department_id,
                branch=branch,
            )
        measurements_ms = (time.perf_counter() - measurements_started) * 1000

        snapshots: list[StrategicIndicatorsPeriodSnapshot] = []
        catalog_started = time.perf_counter()
        build_started = time.perf_counter()

        departments_catalog = self._departments_catalog_repository.list_departments_catalog()
        if department_id:
            departments_catalog = [
                item
                for item in departments_catalog
                if item.department_id == department_id
            ]

        goals_by_department: dict[str, str] = {}
        if hasattr(self._departments_catalog_repository, "get_department_goal_summary"):
            goals_by_department = self._departments_catalog_repository.get_department_goal_summary()
        if department_id:
            goals_by_department = {
                key: value
                for key, value in goals_by_department.items()
                if key == department_id
            }

        for period in periods:
            indicators_catalog = (
                self._resolved_indicators_catalog_repository.list_resolved_indicators_catalog(
                    competence=period.competence,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    department_id=department_id,
                )
            )
            catalog = StrategicIndicatorsCatalogSnapshot(
                departments_catalog=departments_catalog,
                indicators_catalog=indicators_catalog,
                goals_by_department=goals_by_department,
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

        catalog_ms = (time.perf_counter() - catalog_started) * 1000
        build_ms = (time.perf_counter() - build_started) * 1000
        total_ms = (time.perf_counter() - started) * 1000
        logger.info(
            (
                "si_series_snapshot periods=%d department_id=%s branch=%s "
                "measurements_ms=%.0f catalog_ms=%.0f build_ms=%.0f total_ms=%.0f"
            ),
            len(periods),
            department_id,
            branch,
            measurements_ms,
            catalog_ms,
            build_ms,
            total_ms,
        )
        return snapshots

    def _load_measurements_by_period_parallel(
        self,
        *,
        periods: list[ResolvedPeriod],
        department_id: str | None,
        branch: str | None,
    ) -> dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]]:
        max_workers = min(len(periods), 3)

        def load_period(
            period: ResolvedPeriod,
        ) -> tuple[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]]:
            port = self._measurements_port_factory()
            measurements = self._get_measurements(
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
                department_id=department_id,
                branch=branch,
                measurements_port=port,
            )
            return period.competence, measurements

        merged: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(load_period, period) for period in periods]
            for future in futures:
                competence, measurements = future.result()
                merged[competence] = measurements

        return merged

    def _get_measurements(
        self,
        *,
        start_date: str,
        end_date: str,
        competence: str | None,
        department_id: str | None,
        branch: str | None,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        key = measurements_cache_key(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            department_id=department_id,
            branch=branch,
        )

        cached = self._measurements_cache.get(key)
        if cached is not None:
            return cached

        cached = shared_measurements_cache.get(key)
        if cached is not None:
            self._measurements_cache[key] = cached
            return cached

        port = measurements_port or self._measurements_port
        measurements_started = time.perf_counter()
        result = port.get_measurements(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            department_id=department_id,
            branch=branch,
        )
        self._measurements_cache[key] = result
        shared_measurements_cache.set(key, result)
        items, errors = result
        logger.info(
            (
                "si_measurements_loaded competence=%s department_id=%s branch=%s "
                "items=%d errors=%d ms=%.0f"
            ),
            competence,
            department_id,
            branch,
            len(items),
            len(errors),
            (time.perf_counter() - measurements_started) * 1000,
        )
        return result