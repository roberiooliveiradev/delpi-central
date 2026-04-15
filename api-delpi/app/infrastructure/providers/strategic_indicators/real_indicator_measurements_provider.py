from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Callable

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.quality_indicators_snapshot_port import (
    StrategicIndicatorsQualityIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.hr_indicators_snapshot_port import (
    StrategicIndicatorsHrIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.financial_indicators_snapshot_port import (
    StrategicIndicatorsFinancialIndicatorsSnapshotPort,
)
from app.domain.ports.strategic_indicators.supplies_indicators_snapshot_port import (
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
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
            tuple[str | None, str | None, str | None, str | None],
            tuple[list[StrategicIndicatorMeasuredValue], list[dict]],
        ] = {}

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
            department_id=department_id,
            branch=branch,
        )

    def get_indicator_measurements(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> tuple[list[StrategicIndicatorMeasuredValue], list[dict]]:
        cache_key = (start_date, end_date, department_id, branch)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        collectors = self._build_collectors(
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )

        raw_results = self._collect_parallel(collectors)

        items: list[StrategicIndicatorMeasuredValue] = []
        errors: list[dict] = []

        for result in raw_results:
            self._append_result(
                result=result,
                items=items,
                errors=errors,
            )

        final_result = (items, errors)
        self._cache[cache_key] = final_result
        return final_result

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
                executor.submit(fetcher): name
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
            items.append(
                StrategicIndicatorMeasuredValue(
                    indicator_id=raw["indicator_id"],
                    department_id=raw["department_id"],
                    value=float(raw["value"]),
                    source=raw["source"],
                    unit_values=raw.get("unit_values"),
                )
            )

        errors.extend(result.get("errors", []))