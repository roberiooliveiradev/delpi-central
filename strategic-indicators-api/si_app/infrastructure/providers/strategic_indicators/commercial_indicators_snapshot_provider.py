from __future__ import annotations

from si_app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)
from si_app.shared.branch_filter import build_unit_values_for_consolidated_department


class CommercialIndicatorsSnapshotProvider(
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        commercial_metrics_snapshot_service: CommercialMetricsSnapshotService,
    ) -> None:
        self._commercial_metrics_snapshot_service = commercial_metrics_snapshot_service

    def get_commercial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._commercial_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
                branch=None,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "commercial",
                        "source": f"commercial_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(snapshot=snapshot, view_branch=branch)

    def get_commercial_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._commercial_metrics_snapshot_service.get_snapshot_series(
                periods=periods,
                branch=None,
            )
        except Exception as exc:
            scope = branch or "consolidated"
            return {
                period.competence: {
                    "items": [],
                    "errors": [
                        {
                            "department_id": "commercial",
                            "source": f"commercial_snapshot_{scope}",
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

            result[period.competence] = self._map_snapshot_to_result(
                snapshot=snapshot,
                view_branch=branch,
            )

        return result

    def _map_snapshot_to_result(
        self,
        *,
        snapshot,
        view_branch: str | None = None,
    ) -> dict:
        return {
            "items": [
                self._build_measurement(
                    indicator_id="commercial-rol-matrix",
                    source="commercial_head_office_rol_target",
                    value=snapshot.matrix_rol_value,
                    unit_values={"matrix": snapshot.matrix_rol_value},
                ),
                self._build_measurement(
                    indicator_id="commercial-rol-branch",
                    source="commercial_branch_rol_target",
                    value=snapshot.branch_rol_value,
                    unit_values={"branch": snapshot.branch_rol_value},
                ),
                self._build_consolidated_measurement(
                    indicator_id="commercial-closing-rate",
                    source="commercial_sales_conversion_rate",
                    value=snapshot.sales_conversion_rate_pct,
                    view_branch=view_branch,
                ),
                self._build_consolidated_measurement(
                    indicator_id="commercial-sales-order-otd",
                    source="commercial_sales_order_otd",
                    value=snapshot.sales_order_otd_pct,
                    view_branch=view_branch,
                ),
                self._build_consolidated_measurement(
                    indicator_id="commercial-new-business-rol",
                    source="commercial_new_business_rol_pct",
                    value=snapshot.new_business_rol_pct,
                    view_branch=view_branch,
                ),
            ],
            "errors": [],
        }

    def _build_consolidated_measurement(
        self,
        *,
        indicator_id: str,
        source: str,
        value: float | None,
        view_branch: str | None,
    ) -> dict:
        return self._build_measurement(
            indicator_id=indicator_id,
            source=source,
            value=value,
            unit_values=build_unit_values_for_consolidated_department(
                consolidated_value=value,
                view_branch=view_branch,
            ),
        )

    def _build_measurement(
        self,
        *,
        indicator_id: str,
        source: str,
        value: float | None,
        unit_values: dict[str, float | None],
    ) -> dict:
        return {
            "department_id": "commercial",
            "indicator_id": indicator_id,
            "value": value,
            "source": source,
            "unit_values": unit_values,
        }