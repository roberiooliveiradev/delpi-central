from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from si_app.infrastructure.concurrency.context_thread import submit_in_request_context
from collections.abc import Callable

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.config import settings
from si_app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from si_app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.quality_indicators_snapshot_port import (
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.hr_indicators_snapshot_port import (
    StrategicIndicatorsHrIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.financial_indicators_snapshot_port import (
    StrategicIndicatorsFinancialIndicatorsSnapshotPort,
)
from si_app.domain.ports.strategic_indicators.supplies_indicators_snapshot_port import (
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
)
from si_app.application.services.strategic_indicators.measurement_snapshot_versions import (
    failed_department_ids_from_errors,
)
from si_app.application.services.strategic_indicators.measurements_cache_policy import (
    enrich_measurement_errors,
)
from si_app.application.services.strategic_indicators.snapshot_shared_cache import (
    measurements_cache_key,
)
from si_app.application.services.strategic_indicators.versioned_measurements_cache import (
    get_versioned_measurements,
)


class RealStrategicIndicatorsMeasurementsProvider(
    StrategicIndicatorsIndicatorMeasurementsPort,
):
    def __init__(
        self,
        *,
        engineering_snapshot_port: StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
        production_snapshot_port: StrategicIndicatorsProductionIndicatorsSnapshotPort,
        commercial_snapshot_port: StrategicIndicatorsCommercialIndicatorsSnapshotPort,
        quality_snapshot_port: StrategicIndicatorsQualityIndicatorsSnapshotPort,
        hr_snapshot_port: StrategicIndicatorsHrIndicatorsSnapshotPort | None = None,
        financial_snapshot_port: StrategicIndicatorsFinancialIndicatorsSnapshotPort | None = None,
        supplies_snapshot_port: StrategicIndicatorsSuppliesIndicatorsSnapshotPort | None = None,
    ) -> None:
        self._engineering_snapshot_port = engineering_snapshot_port
        self._production_snapshot_port = production_snapshot_port
        self._commercial_snapshot_port = commercial_snapshot_port
        self._quality_snapshot_port = quality_snapshot_port
        self._hr_snapshot_port = hr_snapshot_port
        self._financial_snapshot_port = financial_snapshot_port
        self._supplies_snapshot_port = supplies_snapshot_port
        self._cache: dict[
            str,
            tuple[list[StrategicIndicatorMeasuredValue], list[dict]],
        ] = {}
        self._cache_lock = threading.Lock()

    def get_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        return self.get_indicator_measurements(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            department_id=department_id,
            branch=branch,
        )

    def get_indicator_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        competence: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        cache_key = measurements_cache_key(
            start_date=start_date or "",
            end_date=end_date or "",
            competence=competence,
            department_id=department_id,
            branch=branch,
        )
        with self._cache_lock:
            cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        versioned = get_versioned_measurements(cache_key, department_id=department_id)
        if versioned is not None:
            final_result = (versioned.items, versioned.errors)
            with self._cache_lock:
                self._cache[cache_key] = final_result
            return final_result

        collectors = self._build_collectors(
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )

        items, errors = self._collect_measurements_from_collectors(
            collectors,
            department_id=department_id,
            competence=competence,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        final_result = (items, errors)
        with self._cache_lock:
            self._cache[cache_key] = final_result
        return final_result

    def get_indicator_measurements_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        department_id: str | None = None,
        branch: str | None = None,
    ) -> dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]]:
        if (
            department_id == "hr"
            and self._hr_snapshot_port is not None
            and hasattr(self._hr_snapshot_port, "get_hr_indicators_snapshot_series")
        ):
            raw_series = self._hr_snapshot_port.get_hr_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if (
            department_id == "financial"
            and self._financial_snapshot_port is not None
            and hasattr(self._financial_snapshot_port, "get_financial_indicators_snapshot_series")
        ):
            raw_series = self._financial_snapshot_port.get_financial_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if (
            department_id == "quality"
            and self._quality_snapshot_port is not None
            and hasattr(self._quality_snapshot_port, "get_quality_indicators_snapshot_series")
        ):
            raw_series = self._quality_snapshot_port.get_quality_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}

        if (
            department_id == "production"
            and self._production_snapshot_port is not None
            and hasattr(self._production_snapshot_port, "get_production_indicators_snapshot_series")
        ):
            raw_series = self._production_snapshot_port.get_production_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if (
            department_id == "supplies"
            and self._supplies_snapshot_port is not None
            and hasattr(self._supplies_snapshot_port, "get_supplies_indicators_snapshot_series")
        ):
            raw_series = self._supplies_snapshot_port.get_supplies_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if (
            department_id == "commercial"
            and self._commercial_snapshot_port is not None
            and hasattr(self._commercial_snapshot_port, "get_commercial_indicators_snapshot_series")
        ):
            raw_series = self._commercial_snapshot_port.get_commercial_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if (
            department_id == "engineering"
            and self._engineering_snapshot_port is not None
            and hasattr(self._engineering_snapshot_port, "get_engineering_indicators_snapshot_series")
        ):
            raw_series = self._engineering_snapshot_port.get_engineering_indicators_snapshot_series(
                periods=periods,
                branch=branch,
            )

            result: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for competence, raw in raw_series.items():
                items: list[StrategicIndicatorMeasuredValue] = []
                errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=items,
                    errors=errors,
                )
                result[competence] = (items, errors)

            return result

        if department_id in (None, ""):
            return self._get_consolidated_indicator_measurements_series(
                periods=periods,
                branch=branch,
            )

        for period in periods:
            result[period.competence] = self.get_indicator_measurements(
                start_date=period.start_date,
                end_date=period.end_date,
                department_id=department_id,
                branch=branch,
            )

        return result

    def _get_consolidated_indicator_measurements_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None,
    ) -> dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]]:
        series_collectors: list[tuple[str, Callable[[], dict[str, dict]]]] = []

        if self._engineering_snapshot_port is not None and hasattr(
            self._engineering_snapshot_port,
            "get_engineering_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "engineering",
                    lambda: self._engineering_snapshot_port.get_engineering_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._production_snapshot_port is not None and hasattr(
            self._production_snapshot_port,
            "get_production_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "production",
                    lambda: self._production_snapshot_port.get_production_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._commercial_snapshot_port is not None and hasattr(
            self._commercial_snapshot_port,
            "get_commercial_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "commercial",
                    lambda: self._commercial_snapshot_port.get_commercial_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._quality_snapshot_port is not None and hasattr(
            self._quality_snapshot_port,
            "get_quality_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "quality",
                    lambda: self._quality_snapshot_port.get_quality_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._hr_snapshot_port is not None and hasattr(
            self._hr_snapshot_port,
            "get_hr_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "hr",
                    lambda: self._hr_snapshot_port.get_hr_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._financial_snapshot_port is not None and hasattr(
            self._financial_snapshot_port,
            "get_financial_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "financial",
                    lambda: self._financial_snapshot_port.get_financial_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if self._supplies_snapshot_port is not None and hasattr(
            self._supplies_snapshot_port,
            "get_supplies_indicators_snapshot_series",
        ):
            series_collectors.append(
                (
                    "supplies",
                    lambda: self._supplies_snapshot_port.get_supplies_indicators_snapshot_series(
                        periods=periods,
                        branch=branch,
                    ),
                )
            )

        if not series_collectors:
            merged: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {}
            for period in periods:
                merged[period.competence] = self.get_indicator_measurements(
                    start_date=period.start_date,
                    end_date=period.end_date,
                    department_id=None,
                    branch=branch,
                )
            return merged

        merged_results: dict[str, tuple[list[StrategicIndicatorMeasuredValue], list[dict]]] = {
            period.competence: ([], []) for period in periods
        }

        if len(series_collectors) == 1:
            dept_series = [series_collectors[0][1]()]
        else:
            dept_series = []
            max_department_workers = min(
                len(series_collectors),
                max(1, int(getattr(settings, "SI_SERIES_MAX_PARALLEL_PERIODS", 2) or 2)),
            )
            with ThreadPoolExecutor(max_workers=max_department_workers) as executor:
                future_map = {
                    submit_in_request_context(executor, fetcher): name
                    for name, fetcher in series_collectors
                }
                for future in as_completed(future_map):
                    name = future_map[future]
                    try:
                        dept_series.append(future.result())
                    except Exception as exc:
                        dept_series.append(
                            {
                                period.competence: {
                                    "items": [],
                                    "errors": [
                                        {
                                            "department_id": name,
                                            "source": f"{name}_snapshot_series",
                                            "message": str(exc),
                                        }
                                    ],
                                }
                                for period in periods
                            }
                        )

        for raw_series in dept_series:
            for competence, raw in raw_series.items():
                items, errors = merged_results.setdefault(competence, ([], []))
                bucket_items: list[StrategicIndicatorMeasuredValue] = []
                bucket_errors: list[dict] = []
                self._append_result(
                    result=raw,
                    items=bucket_items,
                    errors=bucket_errors,
                )
                items.extend(bucket_items)
                errors.extend(bucket_errors)

        return merged_results

    def _build_collectors(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        department_id: str | None,
        branch: str | None,
    ) -> list[tuple[str, Callable[[], dict]]]:
        collectors: list[tuple[str, Callable[[], dict]]] = []

        if department_id in (None, "", "engineering"):
            collectors.append(
                (
                    "engineering",
                    lambda: self._engineering_snapshot_port.get_engineering_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if department_id in (None, "", "production"):
            collectors.append(
                (
                    "production",
                    lambda: self._production_snapshot_port.get_production_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if department_id in (None, "", "commercial"):
            collectors.append(
                (
                    "commercial",
                    lambda: self._commercial_snapshot_port.get_commercial_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if department_id in (None, "", "quality"):
            collectors.append(
                (
                    "quality",
                    lambda: self._quality_snapshot_port.get_quality_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if self._hr_snapshot_port is not None and department_id in (None, "", "hr"):
            collectors.append(
                (
                    "hr",
                    lambda: self._hr_snapshot_port.get_hr_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if self._financial_snapshot_port is not None and department_id in (None, "", "financial"):
            collectors.append(
                (
                    "financial",
                    lambda: self._financial_snapshot_port.get_financial_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        if self._supplies_snapshot_port is not None and department_id in (None, "", "supplies"):
            collectors.append(
                (
                    "supplies",
                    lambda: self._supplies_snapshot_port.get_supplies_indicators_snapshot(
                        start_date=start_date,
                        end_date=end_date,
                        branch=branch,
                    ),
                )
            )

        return collectors

    def _collect_measurements_from_collectors(
        self,
        collectors: list[tuple[str, Callable[[], dict]]],
        *,
        department_id: str | None,
        competence: str | None,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        raw_results = self._collect_parallel(collectors)

        items: list[StrategicIndicatorMeasuredValue] = []
        errors: list[dict] = []

        for result in raw_results:
            self._append_result(
                result=result,
                items=items,
                errors=errors,
            )

        errors = enrich_measurement_errors(
            items,
            errors,
            department_id=department_id,
            competence=competence,
            branch=branch,
        )

        failed_departments = failed_department_ids_from_errors(errors)
        if failed_departments and department_id in (None, ""):
            retry_collectors = [
                (name, fetcher)
                for name, fetcher in collectors
                if name in failed_departments
            ]
            if retry_collectors:
                retry_results = self._collect_parallel(retry_collectors)
                for (name, _fetcher), result in zip(
                    retry_collectors,
                    retry_results,
                    strict=True,
                ):
                    self._replace_department_measurements(
                        department_id=name,
                        result=result,
                        items=items,
                        errors=errors,
                    )
                errors = enrich_measurement_errors(
                    items,
                    errors,
                    department_id=department_id,
                    competence=competence,
                    branch=branch,
                )

        return items, errors

    def _replace_department_measurements(
        self,
        *,
        department_id: str,
        result: dict,
        items: list[StrategicIndicatorMeasuredValue],
        errors: list[dict],
    ) -> None:
        items[:] = [
            item
            for item in items
            if (item.department_id or "").strip() != department_id
        ]
        errors[:] = [
            entry
            for entry in errors
            if str(entry.get("department_id") or "").strip() != department_id
        ]
        self._append_result(result=result, items=items, errors=errors)

    def _collect_parallel(
        self,
        collectors: list[tuple[str, Callable[[], dict]]],
    ) -> list[dict]:
        if not collectors:
            return []

        if len(collectors) == 1:
            _name, fetcher = collectors[0]
            return [fetcher()]

        results_by_name: dict[str, dict] = {}

        with ThreadPoolExecutor(max_workers=len(collectors)) as executor:
            future_map = {
                submit_in_request_context(executor, fetcher): name
                for name, fetcher in collectors
            }

            for future in as_completed(future_map):
                name = future_map[future]
                try:
                    results_by_name[name] = future.result()
                except Exception as exc:
                    results_by_name[name] = {
                        "items": [],
                        "errors": [
                            {
                                "department_id": name,
                                "source": f"{name}_snapshot",
                                "message": str(exc),
                            }
                        ],
                    }

        ordered_results: list[dict] = []
        for name, _fetcher in collectors:
            ordered_results.append(
                results_by_name.get(name, {"items": [], "errors": []})
            )

        return ordered_results

    def _append_result(
        self,
        *,
        result: dict,
        items: list[StrategicIndicatorMeasuredValue],
        errors: list[dict],
    ) -> None:
        for raw in result.get("items", []):
            raw_value = raw.get("value")
            normalized_value = (
                round(float(raw_value), 2)
                if raw_value is not None
                else None
            )

            raw_unit_values = raw.get("unit_values") or {}
            normalized_unit_values = {
                key: (round(float(value), 2) if value is not None else None)
                for key, value in raw_unit_values.items()
            }

            items.append(
                StrategicIndicatorMeasuredValue(
                    indicator_id=raw["indicator_id"],
                    department_id=raw["department_id"],
                    value=normalized_value,
                    source=raw["source"],
                    unit_values=normalized_unit_values,
                )
            )

        errors.extend(result.get("errors", []))