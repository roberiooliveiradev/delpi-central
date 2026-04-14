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
        branch: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        try:
            snapshot = self._resolve_snapshot(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "production",
                        "source": f"production_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="production-direct-labor",
                source="production_direct_labor",
                snapshot=snapshot,
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
                snapshot=snapshot,
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
                snapshot=snapshot,
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
                snapshot=snapshot,
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
                snapshot=snapshot,
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

    def _resolve_snapshot(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ):
        if branch:
            return self._production_metrics_snapshot_service.get_unit_snapshot(
                branch=branch,
                start_date=start_date,
                end_date=end_date,
            )

        return self._production_metrics_snapshot_service.get_consolidated_snapshot(
            start_date=start_date,
            end_date=end_date,
        )

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
        snapshot,
        value_getter,
    ) -> dict:
        value = value_getter(snapshot)
        normalized_value = float(value) if value is not None else 0.0
        unit_key = snapshot.branch if snapshot.branch else "consolidated"

        return {
            "department_id": "production",
            "indicator_id": indicator_id,
            "value": normalized_value,
            "source": source,
            "unit_values": {
                unit_key: normalized_value,
            },
        }