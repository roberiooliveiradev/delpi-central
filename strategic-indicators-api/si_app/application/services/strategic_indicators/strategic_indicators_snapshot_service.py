from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from si_app.infrastructure.concurrency.context_thread import submit_in_request_context
from typing import Iterable

from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    is_standard_competence_period,
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
from si_app.application.services.strategic_indicators.catalog_inputs_fingerprint import (
    build_catalog_inputs_fingerprint,
)
from si_app.application.services.strategic_indicators.period_scores_serialization import (
    normalize_scope_branch,
    normalize_scope_department_id,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
    StrategicIndicatorsCatalogSnapshot,
    StrategicIndicatorsComparativeSnapshot,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    _catalog_cache as shared_catalog_cache,
    catalog_cache_key,
    get_catalog_fingerprint,
    measurements_cache_key,
    set_catalog_fingerprint,
)
from si_app.application.services.strategic_indicators.measurement_errors import (
    has_transformometro_auth_error,
)
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    enrich_measurement_errors,
    format_measurement_errors_summary,
    should_cache_measurements,
)
from si_app.application.services.strategic_indicators.versioned_measurements_cache import (
    get_versioned_measurements,
    measurement_version_meta_dict,
    record_versioned_measurements,
)
from si_app.config import settings
from si_app.domain.ports.strategic_indicators.calculation_snapshots_repository_port import (
    StrategicIndicatorsCalculationSnapshotsRepositoryPort,
)
from si_app.domain.ports.strategic_indicators.period_scores_repository_port import (
    StrategicIndicatorsPeriodScoresRepositoryPort,
)

logger = logging.getLogger("strategic_indicators.snapshot")


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
        period_scores_repository: StrategicIndicatorsPeriodScoresRepositoryPort | None = None,
        calculation_snapshots_repository: (
            StrategicIndicatorsCalculationSnapshotsRepositoryPort | None
        ) = None,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._resolved_indicators_catalog_repository = resolved_indicators_catalog_repository
        self._measurements_port = measurements_port
        self._measurements_port_factory = measurements_port_factory
        self._period_scores_repository = period_scores_repository
        self._calculation_snapshots_repository = calculation_snapshots_repository
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
            self._ensure_catalog_fingerprint_cached(cache_key, cached)
            logger.debug(
                "si_catalog_cache_hit scope=request competence=%s department_id=%s",
                competence,
                department_id,
            )
            return cached

        cached = shared_catalog_cache.get(cache_key)
        if cached is not None:
            self._catalog_cache[cache_key] = cached
            self._ensure_catalog_fingerprint_cached(cache_key, cached)
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
            branch=branch,
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
        set_catalog_fingerprint(cache_key, build_catalog_inputs_fingerprint(snapshot))
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
        force_compute: bool = False,
    ) -> StrategicIndicatorsPeriodSnapshot:
        started = time.perf_counter()
        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        if not force_compute:
            stored = self._load_stored_period_snapshot(
                period=period,
                department_id=department_id,
                branch=branch,
            )
            if stored is not None and not has_transformometro_auth_error(
                stored.measurement_errors
            ):
                logger.info(
                    "si_period_scores_hit competence=%s department_id=%s branch=%s ms=%.0f",
                    period.competence,
                    department_id,
                    branch,
                    (time.perf_counter() - started) * 1000,
                )
                return stored
            if stored is not None:
                logger.warning(
                    (
                        "si_period_scores_skip_stale_transformometro_auth "
                        "competence=%s department_id=%s branch=%s"
                    ),
                    period.competence,
                    department_id,
                    branch,
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
            branch=branch,
        )
        self._persist_calculation_snapshot(
            period=period,
            catalog=catalog,
            measurements=measurements,
            measurement_errors=measurement_errors,
            department_id=department_id,
            branch=branch,
            on_read_path=True,
        )
        self._persist_period_snapshot(
            snapshot=snapshot,
            department_id=department_id,
            branch=branch,
            catalog=catalog,
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
        force_compute: bool = False,
    ) -> StrategicIndicatorsComparativeSnapshot:
        started = time.perf_counter()
        current_period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        previous_period_resolved = previous_period(current_period)

        if not force_compute:
            stored_current = self._load_stored_period_snapshot(
                period=current_period,
                department_id=department_id,
                branch=branch,
            )
            stored_previous = self._load_stored_period_snapshot(
                period=previous_period_resolved,
                department_id=department_id,
                branch=branch,
            )
            if stored_current is not None and stored_previous is not None:
                catalog = self.get_catalog_snapshot(
                    competence=current_period.competence,
                    start_date=current_period.start_date,
                    end_date=current_period.end_date,
                    department_id=department_id,
                    branch=branch,
                )
                logger.info(
                    (
                        "si_period_scores_hit_comparative current=%s previous=%s "
                        "department_id=%s branch=%s ms=%.0f"
                    ),
                    current_period.competence,
                    previous_period_resolved.competence,
                    department_id,
                    branch,
                    (time.perf_counter() - started) * 1000,
                )
                return StrategicIndicatorsComparativeSnapshot(
                    catalog=catalog,
                    current=stored_current,
                    previous=stored_previous,
                )

            if stored_current is not None or stored_previous is not None:
                return self._get_comparative_with_partial_stored(
                    started=started,
                    current_period=current_period,
                    previous_period_resolved=previous_period_resolved,
                    stored_current=stored_current,
                    stored_previous=stored_previous,
                    department_id=department_id,
                    branch=branch,
                )

        measurements_started = time.perf_counter()
        if self._measurements_port_factory is not None:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_current = submit_in_request_context(
                    executor,
                    lambda: self._get_measurements(
                        start_date=current_period.start_date,
                        end_date=current_period.end_date,
                        competence=current_period.competence,
                        department_id=department_id,
                        branch=branch,
                        measurements_port=self._measurements_port_factory(),
                    ),
                )
                future_previous = submit_in_request_context(
                    executor,
                    lambda: self._get_measurements(
                        start_date=previous_period_resolved.start_date,
                        end_date=previous_period_resolved.end_date,
                        competence=previous_period_resolved.competence,
                        department_id=department_id,
                        branch=branch,
                        measurements_port=self._measurements_port_factory(),
                    ),
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
            branch=branch,
        )
        previous = self._build_period_snapshot(
            period=previous_period_resolved,
            catalog=catalog_previous,
            measurements=measurements_previous,
            measurement_errors=errors_previous,
            department_id=department_id,
            branch=branch,
        )
        self._persist_calculation_snapshot(
            period=current_period,
            catalog=catalog_current,
            measurements=measurements_current,
            measurement_errors=errors_current,
            department_id=department_id,
            branch=branch,
            on_read_path=True,
        )
        self._persist_calculation_snapshot(
            period=previous_period_resolved,
            catalog=catalog_previous,
            measurements=measurements_previous,
            measurement_errors=errors_previous,
            department_id=department_id,
            branch=branch,
            on_read_path=True,
        )
        self._persist_period_snapshot(
            snapshot=current,
            department_id=department_id,
            branch=branch,
            catalog=catalog_current,
        )
        self._persist_period_snapshot(
            snapshot=previous,
            department_id=department_id,
            branch=branch,
            catalog=catalog_previous,
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
        branch: str | None = None,
    ) -> StrategicIndicatorsPeriodSnapshot:
        calculated_indicators = self._calculator.calculate_indicators(
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            department_id=department_id,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            scope_branch=branch,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=catalog.departments_catalog,
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            scope_branch=branch,
            precalculated_indicators=calculated_indicators,
        )

        calculated_departments = self._calculator.reconcile_period_snapshot_departments(
            calculated_departments=calculated_departments,
            calculated_indicators=calculated_indicators,
            indicators_catalog=catalog.indicators_catalog,
            measurements=measurements,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            scope_branch=branch,
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
        force_compute: bool = False,
        prefer_materialized_only: bool = False,
    ) -> list[StrategicIndicatorsPeriodSnapshot]:
        started = time.perf_counter()
        scope_branch = normalize_scope_branch(branch)
        scope_department_id = normalize_scope_department_id(department_id)

        stored_snapshots: dict[str, StrategicIndicatorsPeriodSnapshot] = {}
        if (
            not force_compute
            and settings.SI_PERIOD_SCORES_ENABLED
            and self._period_scores_repository is not None
            and periods
        ):
            stored_entries = self._period_scores_repository.list_period_snapshots(
                competences=[period.competence for period in periods],
                scope_branch=scope_branch,
                scope_department_id=scope_department_id,
            )
            for period in periods:
                entry = stored_entries.get(period.competence)
                if entry is None:
                    continue
                if not self._period_scores_cache_is_current(
                    entry=entry,
                    period=period,
                    department_id=department_id,
                    branch=branch,
                ):
                    continue
                stored_snapshots[period.competence] = entry.snapshot

        periods_to_compute = [
            period
            for period in periods
            if period.competence not in stored_snapshots
        ]

        if prefer_materialized_only and periods_to_compute:
            logger.info(
                (
                    "si_series_snapshot_materialized_only_skip_compute "
                    "missing=%s department_id=%s branch=%s"
                ),
                [period.competence for period in periods_to_compute],
                department_id,
                branch,
            )
            periods_to_compute = []

        measurements_started = time.perf_counter()
        measurements_by_period: dict[
            str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]
        ] = {}

        if periods_to_compute:
            if (
                self._measurements_port_factory is not None
                and len(periods_to_compute) > 1
                and department_id in (None, "")
            ):
                measurements_by_period = self._load_measurements_by_period_parallel(
                    periods=periods_to_compute,
                    department_id=department_id,
                    branch=branch,
                )
            else:
                measurements_by_period = (
                    self._measurements_port.get_indicator_measurements_series(
                        periods=periods_to_compute,
                        department_id=department_id,
                        branch=branch,
                    )
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
            cached_snapshot = stored_snapshots.get(period.competence)
            if cached_snapshot is not None:
                snapshots.append(cached_snapshot)
                continue

            if prefer_materialized_only:
                continue

            indicators_catalog = (
                self._resolved_indicators_catalog_repository.list_resolved_indicators_catalog(
                    competence=period.competence,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    department_id=department_id,
                    branch=branch,
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

            snapshot = self._build_period_snapshot(
                period=period,
                catalog=catalog,
                measurements=measurements,
                measurement_errors=measurement_errors,
                department_id=department_id,
                branch=branch,
            )
            snapshots.append(snapshot)
            self._persist_calculation_snapshot(
                period=period,
                catalog=catalog,
                measurements=measurements,
                measurement_errors=measurement_errors,
                department_id=department_id,
                branch=branch,
                on_read_path=True,
            )
            self._persist_period_snapshot(
                snapshot=snapshot,
                department_id=department_id,
                branch=branch,
                catalog=catalog,
            )

        catalog_ms = (time.perf_counter() - catalog_started) * 1000
        build_ms = (time.perf_counter() - build_started) * 1000
        total_ms = (time.perf_counter() - started) * 1000
        logger.info(
            (
                "si_series_snapshot periods=%d computed=%d cached=%d "
                "department_id=%s branch=%s "
                "measurements_ms=%.0f catalog_ms=%.0f build_ms=%.0f total_ms=%.0f"
            ),
            len(periods),
            len(periods_to_compute),
            len(stored_snapshots),
            department_id,
            branch,
            measurements_ms,
            catalog_ms,
            build_ms,
            total_ms,
        )
        snapshots.sort(key=lambda item: item.period.competence)
        return snapshots

    def _load_stored_period_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        department_id: str | None,
        branch: str | None,
    ) -> StrategicIndicatorsPeriodSnapshot | None:
        if not settings.SI_PERIOD_SCORES_ENABLED:
            return None
        if self._period_scores_repository is None:
            return None
        if not is_standard_competence_period(period):
            return None

        entry = self._period_scores_repository.get_period_snapshot(
            competence=period.competence,
            scope_branch=normalize_scope_branch(branch),
            scope_department_id=normalize_scope_department_id(department_id),
        )
        if entry is None:
            return None

        if not self._period_scores_cache_is_current(
            entry=entry,
            period=period,
            department_id=department_id,
            branch=branch,
        ):
            return None

        return entry.snapshot

    def _period_scores_cache_is_current(
        self,
        *,
        entry: PeriodScoresCacheEntry,
        period: ResolvedPeriod,
        department_id: str | None,
        branch: str | None,
    ) -> bool:
        stored_hash = (entry.catalog_inputs_hash or "").strip()
        if not stored_hash:
            logger.info(
                (
                    "si_period_scores_stale missing_catalog_hash "
                    "competence=%s department_id=%s branch=%s"
                ),
                period.competence,
                department_id,
                branch,
            )
            return False

        current_hash = self._resolve_catalog_fingerprint(
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
            branch=branch,
        )
        if stored_hash == current_hash:
            return True

        logger.info(
            (
                "si_period_scores_stale catalog_hash_mismatch "
                "competence=%s department_id=%s branch=%s "
                "stored=%s current=%s"
            ),
            period.competence,
            department_id,
            branch,
            stored_hash,
            current_hash,
        )
        return False

    @staticmethod
    def _ensure_catalog_fingerprint_cached(
        cache_key: str,
        catalog: StrategicIndicatorsCatalogSnapshot,
    ) -> None:
        if get_catalog_fingerprint(cache_key) is None:
            set_catalog_fingerprint(cache_key, build_catalog_inputs_fingerprint(catalog))

    def _resolve_catalog_fingerprint(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        department_id: str | None,
        branch: str | None,
    ) -> str:
        cache_key = catalog_cache_key(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )
        cached = get_catalog_fingerprint(cache_key)
        if cached is not None:
            return cached

        catalog = self.get_catalog_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )
        fingerprint = build_catalog_inputs_fingerprint(catalog)
        set_catalog_fingerprint(cache_key, fingerprint)
        return fingerprint

    def _get_comparative_with_partial_stored(
        self,
        *,
        started: float,
        current_period: ResolvedPeriod,
        previous_period_resolved: ResolvedPeriod,
        stored_current: StrategicIndicatorsPeriodSnapshot | None,
        stored_previous: StrategicIndicatorsPeriodSnapshot | None,
        department_id: str | None,
        branch: str | None,
    ) -> StrategicIndicatorsComparativeSnapshot:
        if stored_current is not None and stored_previous is None:
            previous = self._compute_and_persist_period(
                period=previous_period_resolved,
                department_id=department_id,
                branch=branch,
            )
            catalog = self.get_catalog_snapshot(
                competence=current_period.competence,
                start_date=current_period.start_date,
                end_date=current_period.end_date,
                department_id=department_id,
                branch=branch,
            )
            logger.info(
                (
                    "si_period_scores_hit_comparative_partial current=cached "
                    "previous=%s department_id=%s branch=%s ms=%.0f"
                ),
                previous_period_resolved.competence,
                department_id,
                branch,
                (time.perf_counter() - started) * 1000,
            )
            return StrategicIndicatorsComparativeSnapshot(
                catalog=catalog,
                current=stored_current,
                previous=previous,
            )

        if stored_previous is not None and stored_current is None:
            current = self._compute_and_persist_period(
                period=current_period,
                department_id=department_id,
                branch=branch,
            )
            catalog = self.get_catalog_snapshot(
                competence=current_period.competence,
                start_date=current_period.start_date,
                end_date=current_period.end_date,
                department_id=department_id,
                branch=branch,
            )
            logger.info(
                (
                    "si_period_scores_hit_comparative_partial current=%s "
                    "previous=cached department_id=%s branch=%s ms=%.0f"
                ),
                current_period.competence,
                department_id,
                branch,
                (time.perf_counter() - started) * 1000,
            )
            return StrategicIndicatorsComparativeSnapshot(
                catalog=catalog,
                current=current,
                previous=stored_previous,
            )

        raise RuntimeError("partial comparative requires one stored period")

    def _compute_and_persist_period(
        self,
        *,
        period: ResolvedPeriod,
        department_id: str | None,
        branch: str | None,
    ) -> StrategicIndicatorsPeriodSnapshot:
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
            branch=branch,
        )
        self._persist_calculation_snapshot(
            period=period,
            catalog=catalog,
            measurements=measurements,
            measurement_errors=measurement_errors,
            department_id=department_id,
            branch=branch,
            on_read_path=True,
        )
        self._persist_period_snapshot(
            snapshot=snapshot,
            department_id=department_id,
            branch=branch,
            catalog=catalog,
        )
        return snapshot

    def _reconcile_stored_period_snapshot(
        self,
        stored: StrategicIndicatorsPeriodSnapshot,
        *,
        indicators_catalog: list | None = None,
        branch: str | None = None,
    ) -> StrategicIndicatorsPeriodSnapshot:
        reconciled_departments = self._calculator.reconcile_period_snapshot_departments(
            calculated_departments=stored.calculated_departments,
            calculated_indicators=stored.calculated_indicators,
            indicators_catalog=indicators_catalog,
            measurements=stored.measurements,
            start_date=stored.period.start_date,
            end_date=stored.period.end_date,
            competence=stored.period.competence,
            scope_branch=branch,
        )
        igd, igd_exact, classification = self._calculator.calculate_igd(
            reconciled_departments
        )

        return StrategicIndicatorsPeriodSnapshot(
            period=stored.period,
            measurements=stored.measurements,
            measurement_errors=stored.measurement_errors,
            calculated_indicators=stored.calculated_indicators,
            calculated_departments=reconciled_departments,
            igd=igd,
            igd_exact=igd_exact,
            classification=classification,
        )

    def _persist_calculation_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        catalog: StrategicIndicatorsCatalogSnapshot,
        measurements: list[StrategicIndicatorMeasuredValue],
        measurement_errors: list[dict],
        department_id: str | None,
        branch: str | None,
        on_read_path: bool = False,
    ) -> None:
        if on_read_path and not settings.SI_PERSIST_CALCULATION_SNAPSHOTS_ON_READ:
            return
        if not settings.SI_CALCULATION_SNAPSHOTS_ENABLED:
            return
        if self._calculation_snapshots_repository is None:
            return
        if not is_standard_competence_period(period):
            return

        catalog_inputs_hash = build_catalog_inputs_fingerprint(catalog)
        self._calculation_snapshots_repository.upsert_calculation_snapshot(
            period=period,
            catalog=catalog,
            measurements=measurements,
            measurement_errors=measurement_errors,
            scope_branch=normalize_scope_branch(branch),
            scope_department_id=normalize_scope_department_id(department_id),
            catalog_inputs_hash=catalog_inputs_hash,
        )

    def _persist_period_snapshot(
        self,
        *,
        snapshot: StrategicIndicatorsPeriodSnapshot,
        department_id: str | None,
        branch: str | None,
        catalog: StrategicIndicatorsCatalogSnapshot | None = None,
    ) -> None:
        if not settings.SI_PERIOD_SCORES_ENABLED:
            return
        if self._period_scores_repository is None:
            return
        if not is_standard_competence_period(snapshot.period):
            return
        catalog_inputs_hash = (
            build_catalog_inputs_fingerprint(catalog) if catalog is not None else None
        )
        is_clean = should_cache_measurements(
            snapshot.measurements,
            snapshot.measurement_errors,
            department_id=department_id,
        )
        self._period_scores_repository.upsert_period_snapshot(
            snapshot=snapshot,
            scope_branch=normalize_scope_branch(branch),
            scope_department_id=normalize_scope_department_id(department_id),
            catalog_inputs_hash=catalog_inputs_hash,
            is_clean=is_clean,
        )

    def peek_measurement_version_meta(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
        department_id: str | None,
        branch: str | None,
    ) -> dict[str, int | bool] | None:
        key = measurements_cache_key(
            start_date=start_date or "",
            end_date=end_date or "",
            competence=competence,
            department_id=department_id,
            branch=branch,
        )
        return measurement_version_meta_dict(
            get_versioned_measurements(key, department_id=department_id),
        )

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
            futures = [
                submit_in_request_context(executor, lambda p=period: load_period(p))
                for period in periods
            ]
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

        versioned = get_versioned_measurements(key, department_id=department_id)
        if versioned is not None:
            result = (versioned.items, versioned.errors)
            self._measurements_cache[key] = result
            return result

        port = measurements_port or self._measurements_port
        measurements_started = time.perf_counter()
        result = port.get_measurements(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            department_id=department_id,
            branch=branch,
        )
        items, errors = result
        errors = enrich_measurement_errors(
            items,
            errors,
            department_id=department_id,
            competence=competence,
            branch=branch,
        )
        served = record_versioned_measurements(
            key,
            items=items,
            errors=errors,
            department_id=department_id,
        )
        result = (served.items, served.errors)
        self._measurements_cache[key] = result
        if not served.is_clean and errors:
            logger.warning(
                (
                    "si_measurements_not_clean competence=%s department_id=%s "
                    "branch=%s items=%d errors=%d detail=%s"
                ),
                competence,
                department_id,
                branch,
                len(items),
                len(errors),
                format_measurement_errors_summary(errors, limit=3),
            )
        if errors:
            logger.warning(
                (
                    "si_measurements_quality_issues competence=%s department_id=%s "
                    "branch=%s errors=%d\n%s"
                ),
                competence,
                department_id,
                branch,
                len(errors),
                format_measurement_errors_summary(errors),
            )
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