from __future__ import annotations

from app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from app.domain.ports.strategic_indicators.engineering_indicators_snapshot_port import (
    StrategicIndicatorsEngineeringIndicatorsSnapshotPort,
)


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
                branch=branch,
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

        unit_key = branch or "consolidated"

        return {
            "items": [
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-projects-on-time",
                    "value": snapshot.lmp_projects_on_time_pct,
                    "source": "lmp",
                    "unit_values": {
                        unit_key: snapshot.lmp_projects_on_time_pct,
                    },
                },
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-transforma-plus",
                    "value": snapshot.transforma_mais_financial_gain,
                    "source": "transforma_mais",
                    "unit_values": {
                        unit_key: snapshot.transforma_mais_financial_gain,
                    },
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
                branch=branch,
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

            unit_key = branch or "consolidated"

            result[period.competence] = {
                "items": [
                    {
                        "department_id": "engineering",
                        "indicator_id": "engineering-projects-on-time",
                        "value": snapshot.lmp_projects_on_time_pct,
                        "source": "lmp",
                        "unit_values": {
                            unit_key: snapshot.lmp_projects_on_time_pct,
                        },
                    },
                    {
                        "department_id": "engineering",
                        "indicator_id": "engineering-transforma-plus",
                        "value": snapshot.transforma_mais_financial_gain,
                        "source": "transforma_mais",
                        "unit_values": {
                            unit_key: snapshot.transforma_mais_financial_gain,
                        },
                    },
                ],
                "errors": [],
            }

        return result