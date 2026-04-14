from __future__ import annotations

from app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshotService,
)
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)


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
        items: list[dict] = []
        errors: list[dict] = []

        try:
            snapshot = self._commercial_metrics_snapshot_service.get_snapshot(
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
                        "department_id": "commercial",
                        "source": f"commercial_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="commercial-rol-matrix",
                source="commercial_head_office_rol_target",
                value=snapshot.matrix_rol_value,
                unit_values={"matrix": snapshot.matrix_rol_value},
            ),
            department_id="commercial",
            source="commercial_head_office_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="commercial-rol-branch",
                source="commercial_branch_rol_target",
                value=snapshot.branch_rol_value,
                unit_values={"branch": snapshot.branch_rol_value},
            ),
            department_id="commercial",
            source="commercial_branch_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="commercial-closing-rate",
                source="commercial_sales_conversion_rate",
                value=snapshot.sales_conversion_rate_pct,
                unit_values={branch or "consolidated": snapshot.sales_conversion_rate_pct},
            ),
            department_id="commercial",
            source="commercial_sales_conversion_rate",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="commercial-new-clients",
                source="commercial_new_clients_average",
                value=snapshot.monthly_average_new_clients,
                unit_values={branch or "consolidated": snapshot.monthly_average_new_clients},
            ),
            department_id="commercial",
            source="commercial_new_clients_average",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_measurement(
                indicator_id="commercial-new-rol",
                source="commercial_new_clients_rol_pct",
                value=snapshot.new_clients_rol_pct,
                unit_values={branch or "consolidated": snapshot.new_clients_rol_pct},
            ),
            department_id="commercial",
            source="commercial_new_clients_rol_pct",
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
        value: float,
        unit_values: dict[str, float],
    ) -> dict:
        return {
            "department_id": "commercial",
            "indicator_id": indicator_id,
            "value": value,
            "source": source,
            "unit_values": unit_values,
        }