from __future__ import annotations

from si_app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)
from si_app.shared.branch_filter import build_unit_values_for_consolidated_department


class EngineeringIndicatorsSnapshotProvider(
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        engineering_metrics_snapshot_service: EngineeringMetricsSnapshotService,
    ) -> None:
        self._engineering_metrics_snapshot_service = engineering_metrics_snapshot_service

    def get_engineering_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._engineering_metrics_snapshot_service.get_snapshot(
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
                        "department_id": "engineering",
                        "source": f"engineering_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        projects_value = snapshot.lmp_projects_on_time_pct
        transforma_value = snapshot.transforma_mais_financial_gain

        return {
            "items": [
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-projects-on-time",
                    "value": projects_value,
                    "source": "lmp",
                    "unit_values": build_unit_values_for_consolidated_department(
                        consolidated_value=projects_value,
                        view_branch=branch,
                    ),
                },
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-transforma-plus",
                    "value": transforma_value,
                    "source": "transforma_mais",
                    "unit_values": build_unit_values_for_consolidated_department(
                        consolidated_value=transforma_value,
                        view_branch=branch,
                    ),
                },
            ],
            "errors": [],
        }

    def get_engineering_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._engineering_metrics_snapshot_service.get_snapshot_series(
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
                            "department_id": "engineering",
                            "source": f"engineering_snapshot_{scope}",
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

            projects_value = snapshot.lmp_projects_on_time_pct
            transforma_value = snapshot.transforma_mais_financial_gain

            result[period.competence] = {
                "items": [
                    {
                        "department_id": "engineering",
                        "indicator_id": "engineering-projects-on-time",
                        "value": projects_value,
                        "source": "lmp",
                        "unit_values": build_unit_values_for_consolidated_department(
                            consolidated_value=projects_value,
                            view_branch=branch,
                        ),
                    },
                    {
                        "department_id": "engineering",
                        "indicator_id": "engineering-transforma-plus",
                        "value": transforma_value,
                        "source": "transforma_mais",
                        "unit_values": build_unit_values_for_consolidated_department(
                            consolidated_value=transforma_value,
                            view_branch=branch,
                        ),
                    },
                ],
                "errors": [],
            }

        return result