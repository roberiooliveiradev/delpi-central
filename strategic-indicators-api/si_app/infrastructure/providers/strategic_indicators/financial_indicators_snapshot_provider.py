from __future__ import annotations

from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.financial_indicators_snapshot_port import (
    StrategicIndicatorsFinancialIndicatorsSnapshotPort,
)
from si_app.shared.branch_filter import (
    FINANCIAL_CONSOLIDATED_BRANCH_KEY,
    build_unit_values_for_consolidated_department,
)


class FinancialIndicatorsSnapshotProvider(
    StrategicIndicatorsFinancialIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        financial_metrics_snapshot_service: FinancialMetricsSnapshotService,
    ) -> None:
        self._financial_metrics_snapshot_service = financial_metrics_snapshot_service

    def get_financial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._financial_metrics_snapshot_service.get_snapshot(
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
                        "department_id": "financial",
                        "source": f"financial_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(
            snapshot=snapshot,
            branch=branch,
        )

    def get_financial_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._financial_metrics_snapshot_service.get_snapshot_series(
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
                            "department_id": "financial",
                            "source": f"financial_snapshot_{scope}",
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
                branch=branch,
            )

        return result

    def _map_snapshot_to_result(
        self,
        *,
        snapshot,
        branch: str | None,
    ) -> dict:
        ebitda_value = self._consolidated_metric(
            snapshot,
            getter=lambda item: item.ebitda_over_rol_pct,
        )
        fixed_cost_value = self._consolidated_metric(
            snapshot,
            getter=lambda item: item.fixed_cost_over_rol_pct,
        )
        pmr_value = self._consolidated_metric(
            snapshot,
            getter=lambda item: item.pmr_days,
        )

        return {
            "items": [
                {
                    "department_id": "financial",
                    "indicator_id": "financial-ebitda",
                    "value": ebitda_value,
                    "source": "financial_ebitda",
                    "unit_values": build_unit_values_for_consolidated_department(
                        consolidated_value=ebitda_value,
                        view_branch=branch,
                    ),
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-fixed-cost",
                    "value": fixed_cost_value,
                    "source": "financial_fixed_cost",
                    "unit_values": build_unit_values_for_consolidated_department(
                        consolidated_value=fixed_cost_value,
                        view_branch=branch,
                    ),
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-pmr",
                    "value": pmr_value,
                    "source": "financial_pmr",
                    "unit_values": build_unit_values_for_consolidated_department(
                        consolidated_value=pmr_value,
                        view_branch=branch,
                    ),
                },
            ],
            "errors": [],
        }

    def _consolidated_metric(self, snapshot, *, getter) -> float | None:
        consolidated_branch = next(
            (
                item
                for item in snapshot.branches
                if item.branch == FINANCIAL_CONSOLIDATED_BRANCH_KEY
            ),
            None,
        )
        if consolidated_branch is not None:
            raw = getter(consolidated_branch)
            return round(float(raw), 2) if raw is not None else None

        valid = [
            float(getter(item))
            for item in snapshot.branches
            if getter(item) is not None
        ]
        if not valid:
            return None

        return round(sum(valid) / len(valid), 2)