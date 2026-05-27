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
from si_app.shared.branch_filter import effective_query_branch
from si_app.shared.goal_scope import BRANCH_UNIT_CODES

MATRIX_BRANCH_CODE = "01"
BRANCH_BRANCH_CODE = "02"


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
            return self._map_snapshot_to_result(
                start_date=start_date,
                end_date=end_date,
                view_branch=branch,
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

    def get_commercial_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}

        for period in periods:
            try:
                result[period.competence] = self._map_snapshot_to_result(
                    start_date=period.start_date,
                    end_date=period.end_date,
                    view_branch=branch,
                )
            except Exception as exc:
                scope = branch or "consolidated"
                result[period.competence] = {
                    "items": [],
                    "errors": [
                        {
                            "department_id": "commercial",
                            "source": f"commercial_snapshot_{scope}",
                            "message": str(exc),
                        }
                    ],
                }

        return result

    def _map_snapshot_to_result(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        view_branch: str | None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        base_snapshot = self._commercial_metrics_snapshot_service.get_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=None,
        )

        self._collect_measurement(
            builder=lambda: self._build_rol_measurement(
                snapshot=base_snapshot,
                view_branch=view_branch,
            ),
            department_id="commercial",
            source="commercial_rol",
            items=items,
            errors=errors,
        )

        per_unit_specs = (
            (
                "commercial-closing-rate",
                "commercial_sales_conversion_rate",
                lambda snap: snap.sales_conversion_rate_pct,
            ),
            (
                "commercial-sales-order-otd",
                "commercial_sales_order_otd",
                lambda snap: snap.sales_order_otd_pct,
            ),
            (
                "commercial-new-business-rol",
                "commercial_new_business_rol_pct",
                lambda snap: snap.new_business_rol_pct,
            ),
        )
        for indicator_id, source, branch_getter in per_unit_specs:
            self._collect_measurement(
                builder=self._per_unit_builder(
                    indicator_id=indicator_id,
                    source=source,
                    branch_getter=branch_getter,
                    base_snapshot=base_snapshot,
                    start_date=start_date,
                    end_date=end_date,
                    view_branch=view_branch,
                ),
                department_id="commercial",
                source=source,
                items=items,
                errors=errors,
            )

        return {
            "items": items,
            "errors": errors,
        }

    def _per_unit_builder(
        self,
        *,
        indicator_id: str,
        source: str,
        branch_getter,
        base_snapshot,
        start_date: str | None,
        end_date: str | None,
        view_branch: str | None,
    ):
        def builder() -> dict:
            return self._build_per_unit_measurement(
                indicator_id=indicator_id,
                source=source,
                base_snapshot=base_snapshot,
                value_getter=branch_getter,
                start_date=start_date,
                end_date=end_date,
                view_branch=view_branch,
            )

        return builder

    def _build_rol_measurement(
        self,
        *,
        snapshot,
        view_branch: str | None,
    ) -> dict:
        unit_values = {
            MATRIX_BRANCH_CODE: snapshot.matrix_rol_value,
            BRANCH_BRANCH_CODE: snapshot.branch_rol_value,
        }
        active_branch = effective_query_branch(view_branch)
        consolidated_value = (
            unit_values.get(active_branch)
            if active_branch
            else None
        )

        return self._build_measurement(
            indicator_id="commercial-rol",
            source="commercial_rol",
            value=consolidated_value,
            unit_values=unit_values,
        )

    def _build_per_unit_measurement(
        self,
        *,
        indicator_id: str,
        source: str,
        base_snapshot,
        value_getter,
        start_date: str | None,
        end_date: str | None,
        view_branch: str | None,
    ) -> dict:
        active_branch = effective_query_branch(view_branch)
        unit_values: dict[str, float | None] = {}

        if active_branch:
            branch_snapshot = self._commercial_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
                branch=active_branch,
            )
            raw = value_getter(branch_snapshot)
            normalized = float(raw) if raw is not None else None
            unit_values[active_branch] = normalized
            return self._build_measurement(
                indicator_id=indicator_id,
                source=source,
                value=normalized,
                unit_values=unit_values,
            )

        for branch_code in BRANCH_UNIT_CODES:
            try:
                branch_snapshot = self._commercial_metrics_snapshot_service.get_snapshot(
                    start_date=start_date,
                    end_date=end_date,
                    branch=branch_code,
                )
                raw = value_getter(branch_snapshot)
                unit_values[branch_code] = float(raw) if raw is not None else None
            except Exception:
                unit_values[branch_code] = None

        return self._build_measurement(
            indicator_id=indicator_id,
            source=source,
            value=None,
            unit_values=unit_values,
        )

    def _collect_measurement(
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
