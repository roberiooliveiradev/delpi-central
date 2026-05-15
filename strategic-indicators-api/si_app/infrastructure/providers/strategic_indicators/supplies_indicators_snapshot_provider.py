from __future__ import annotations

from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.supplies_indicators_snapshot_port import (
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
)


class SuppliesIndicatorsSnapshotProvider(
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        supplies_metrics_snapshot_service: SuppliesMetricsSnapshotService,
    ) -> None:
        self._supplies_metrics_snapshot_service = supplies_metrics_snapshot_service

    def get_supplies_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._supplies_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "supplies",
                        "source": f"supplies_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(snapshot=snapshot)

    def get_supplies_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._supplies_metrics_snapshot_service.get_snapshot_series(
                periods=periods,
                branch=branch,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                period.competence: {
                    "items": [],
                    "errors": [
                        {
                            "department_id": "supplies",
                            "source": f"supplies_snapshot_{scope}",
                            "message": str(exc),
                        }
                    ],
                }
                for period in periods
            }

        result: dict[str, dict] = {}

        for period in periods:
            snapshot = snapshots.get(period.competence)
            if snapshot is None:
                result[period.competence] = {"items": [], "errors": []}
                continue

            result[period.competence] = self._map_snapshot_to_result(snapshot=snapshot)

        return result

    def _map_snapshot_to_result(self, *, snapshot) -> dict:
        unit_key = snapshot.branch or "consolidated"

        return {
            "items": [
                {
                    "department_id": "supplies",
                    "indicator_id": "supplies-cpv",
                    "value": snapshot.cpv_pct,
                    "source": "supplies_cpv",
                    "unit_values": {unit_key: snapshot.cpv_pct},
                },
                {
                    "department_id": "supplies",
                    "indicator_id": "supplies-stock-turnover",
                    "value": snapshot.inventory_turnover_months,
                    "source": "supplies_inventory_turnover",
                    "unit_values": {unit_key: snapshot.inventory_turnover_months},
                },
                {
                    "department_id": "supplies",
                    "indicator_id": "supplies-otd",
                    "value": snapshot.otd_pct,
                    "source": "supplies_otd",
                    "unit_values": {unit_key: snapshot.otd_pct},
                },
                {
                    "department_id": "supplies",
                    "indicator_id": "supplies-stock-value",
                    "value": snapshot.stock_value,
                    "source": "supplies_stock_value",
                    "unit_values": {unit_key: snapshot.stock_value},
                },
            ],
            "errors": [],
        }