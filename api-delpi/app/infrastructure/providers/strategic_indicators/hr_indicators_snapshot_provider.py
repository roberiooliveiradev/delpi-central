from __future__ import annotations

from app.application.services.hr.hr_metrics_snapshot_service import (
    HrMetricsSnapshotService,
)
from app.domain.ports.strategic_indicators.hr_indicators_snapshot_port import (
    StrategicIndicatorsHrIndicatorsSnapshotPort,
)


class HrIndicatorsSnapshotProvider(
    StrategicIndicatorsHrIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        hr_metrics_snapshot_service: HrMetricsSnapshotService,
    ) -> None:
        self._hr_metrics_snapshot_service = hr_metrics_snapshot_service

    def get_hr_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        try:
            snapshot = self._hr_metrics_snapshot_service.get_snapshot(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            return {
                "items": [],
                "errors": [
                    {
                        "department_id": "hr",
                        "source": "hr_snapshot",
                        "message": str(exc),
                    }
                ],
            }

        absenteeism_unit_values = {
            item.branch_code: item.absenteeism_pct for item in snapshot.branches
        }
        turnover_unit_values = {
            item.branch_code: item.turnover_pct for item in snapshot.branches
        }
        training_unit_values = {
            item.branch_code: item.training_hours_per_collaborator
            for item in snapshot.branches
        }

        items = [
            {
                "department_id": "hr",
                "indicator_id": "hr-absenteeism",
                "value": self._average_branch_values(absenteeism_unit_values),
                "source": "portal_rh_absenteeism",
                "unit_values": absenteeism_unit_values,
            },
            {
                "department_id": "hr",
                "indicator_id": "hr-turnover",
                "value": self._average_branch_values(turnover_unit_values),
                "source": "portal_rh_turnover",
                "unit_values": turnover_unit_values,
            },
            {
                "department_id": "hr",
                "indicator_id": "hr-training-hours",
                "value": self._average_branch_values(training_unit_values),
                "source": "portal_rh_training",
                "unit_values": training_unit_values,
            },
        ]

        if snapshot.internal_satisfaction_pct is not None:
            items.append(
                {
                    "department_id": "hr",
                    "indicator_id": "hr-internal-satisfaction",
                    "value": float(snapshot.internal_satisfaction_pct),
                    "source": "portal_rh_satisfaction",
                    "unit_values": {"consolidated": float(snapshot.internal_satisfaction_pct)},
                }
            )

        if snapshot.active_pdi_pct is not None:
            items.append(
                {
                    "department_id": "hr",
                    "indicator_id": "hr-active-pdi",
                    "value": float(snapshot.active_pdi_pct),
                    "source": "portal_rh_pdi",
                    "unit_values": {"consolidated": float(snapshot.active_pdi_pct)},
                }
            )

        return {
            "items": items,
            "errors": [],
        }

    def _average_branch_values(self, values: dict[str, float]) -> float:
        valid = [float(value) for value in values.values()]
        if not valid:
            return 0.0
        return round(sum(valid) / len(valid), 2)