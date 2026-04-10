from __future__ import annotations

from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from app.domain.ports.strategic_indicators.financial_indicators_snapshot_port import (
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
    ) -> dict:
        try:
            snapshot = self._financial_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "financial",
                        "source": "financial_snapshot",
                        "message": str(exc),
                    }
                ],
            }

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
                    "value": self._average_branch_values(ebitda_unit_values),
                    "source": "financial_ebitda",
                    "unit_values": ebitda_unit_values,
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-fixed-cost",
                    "value": self._average_branch_values(fixed_cost_unit_values),
                    "source": "financial_fixed_cost",
                    "unit_values": fixed_cost_unit_values,
                },
                {
                    "department_id": "financial",
                    "indicator_id": "financial-pmr",
                    "value": self._average_branch_values(pmr_unit_values),
                    "source": "financial_pmr",
                    "unit_values": pmr_unit_values,
                },
            ],
            "errors": [],
        }

    def _average_branch_values(self, values: dict[str, float]) -> float:
        valid = [float(value) for value in values.values()]
        if not valid:
            return 0.0
        return round(sum(valid) / len(valid), 2)