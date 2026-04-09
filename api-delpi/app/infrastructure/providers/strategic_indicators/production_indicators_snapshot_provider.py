from __future__ import annotations

from app.application.services.production.production_metrics_snapshot_service import (
    ProductionMetricsSnapshotService,
)
from app.domain.ports.strategic_indicators.production_indicators_snapshot_port import (
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
)


class ProductionIndicatorsSnapshotProvider(
    StrategicIndicatorsProductionIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        production_metrics_snapshot_service: ProductionMetricsSnapshotService,
    ) -> None:
        self._production_metrics_snapshot_service = production_metrics_snapshot_service

    def get_production_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        unit_snapshots: dict[str, object] = {}

        for unit_id, branch in (("matrix", "01"), ("branch", "02")):
            try:
                unit_snapshots[unit_id] = self._production_metrics_snapshot_service.get_unit_snapshot(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as exc:
                errors.append(
                    {
                        "department_id": "production",
                        "source": f"production_unit_{unit_id}",
                        "message": str(exc),
                    }
                )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-direct-labor",
                source="production_direct_labor",
                unit_snapshots=unit_snapshots,
                value_getter=lambda item: item.direct_labor_cost_pct,
            ),
            department_id="production",
            source="production_direct_labor",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-costs",
                source="production_cost",
                unit_snapshots=unit_snapshots,
                value_getter=lambda item: item.production_cost_pct,
            ),
            department_id="production",
            source="production_cost",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-depreciation",
                source="production_depreciation",
                unit_snapshots=unit_snapshots,
                value_getter=lambda item: item.depreciation_pct,
            ),
            department_id="production",
            source="production_depreciation",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-oee",
                source="production_oee",
                unit_snapshots=unit_snapshots,
                value_getter=lambda item: item.oee_pct,
            ),
            department_id="production",
            source="production_oee",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-otd",
                source="production_otd",
                unit_snapshots=unit_snapshots,
                value_getter=lambda item: item.otd_pct,
            ),
            department_id="production",
            source="production_otd",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def _collect_indicator(
        self,
        *,
        builder,
        department_id: str,
        source: str,
        items: list[dict],
        errors: list[dict],
    ) -> None:
        try:
            items.append(builder())
        except Exception as exc:
            errors.append(
                {
                    "department_id": department_id,
                    "source": source,
                    "message": str(exc),
                }
            )

    def _build_measurement(
        self,
        *,
        indicator_id: str,
        source: str,
        unit_snapshots: dict[str, object],
        value_getter,
    ) -> dict:
        matrix_snapshot = unit_snapshots.get("matrix")
        branch_snapshot = unit_snapshots.get("branch")

        matrix_value = value_getter(matrix_snapshot) if matrix_snapshot else 0.0
        branch_value = value_getter(branch_snapshot) if branch_snapshot else 0.0

        value = self._average_values(matrix_value, branch_value) or 0.0

        return {
            "department_id": "production",
            "indicator_id": indicator_id,
            "value": value,
            "source": source,
            "unit_values": {
                "matrix": matrix_value or 0.0,
                "branch": branch_value or 0.0,
            },
        }

    def _average_values(
        self,
        first: float | None,
        second: float | None,
    ) -> float | None:
        valid = [value for value in [first, second] if value is not None]
        if not valid:
            return None
        return round(sum(valid) / len(valid), 2)