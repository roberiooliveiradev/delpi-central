from __future__ import annotations

from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.financial_indicators_snapshot_port import (
    StrategicIndicatorsFinancialIndicatorsSnapshotPort,
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
                branch=branch,
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
                branch=branch,
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
        ebitda_unit_values = {
            item.branch: item.ebitda_over_rol_pct for item in snapshot.branches
        }
        fixed_cost_unit_values = {
            item.branch: item.fixed_cost_over_rol_pct for item in snapshot.branches
        }
        pmr_unit_values = {
            item.branch: item.pmr_days for item in snapshot.branches
        }

        return {
            "items": [
                {
                    "department_id": "financial",
                    "indicator_id": "financial-ebitda",
                    "value": self._resolve_indicator_value(
                        unit_values=ebitda_unit_values,
                        branch=branch,
                    ),
                    "source": "financial_ebitda",
                    "unit_values": ebitda_unit_values,
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-fixed-cost",
                    "value": self._resolve_indicator_value(
                        unit_values=fixed_cost_unit_values,
                        branch=branch,
                    ),
                    "source": "financial_fixed_cost",
                    "unit_values": fixed_cost_unit_values,
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-pmr",
                    "value": self._resolve_indicator_value(
                        unit_values=pmr_unit_values,
                        branch=branch,
                    ),
                    "source": "financial_pmr",
                    "unit_values": pmr_unit_values,
                },
            ],
            "errors": [],
        }

    def _resolve_indicator_value(
        self,
        *,
        unit_values: dict[str, float | None],
        branch: str | None,
    ) -> float | None:
        if branch:
            value = unit_values.get(branch)
            return round(float(value), 2) if value is not None else None

        valid = [float(value) for value in unit_values.values() if value is not None]
        if not valid:
            return None

        return round(sum(valid) / len(valid), 2)