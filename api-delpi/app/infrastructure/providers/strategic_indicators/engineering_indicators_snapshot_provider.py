from __future__ import annotations

from app.application.services.engineering.engineering_metrics_snapshot_service import (
    EngineeringMetricsSnapshotService,
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
    ) -> dict:
        try:
            snapshot = self._engineering_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "engineering",
                        "source": "engineering_snapshot",
                        "message": str(exc),
                    }
                ],
            }

        return {
            "items": [
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-projects-on-time",
                    "value": snapshot.lmp_projects_on_time_pct,
                    "source": "lmp",
                    "unit_values": None,
                },
                {
                    "department_id": "engineering",
                    "indicator_id": "engineering-transforma-plus",
                    "value": snapshot.transforma_mais_financial_gain,
                    "source": "transforma_mais",
                    "unit_values": None,
                },
            ],
            "errors": [],
        }