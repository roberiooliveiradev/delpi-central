from __future__ import annotations

from app.application.services.hr.hr_metrics_snapshot_service import (
    HrMetricsSnapshotService,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
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
        branch: str | None = None,
    ) -> dict:
        try:
            snapshot = self._hr_metrics_snapshot_service.get_snapshot(
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
                        "department_id": "hr",
                        "source": f"hr_snapshot_{scope}",
                        "message": str(exc),
                    }
                ],
            }

        return self._map_snapshot_to_result(
            snapshot=snapshot,
            branch=branch,
        )

    def get_hr_indicators_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, dict]:
        try:
            snapshots = self._hr_metrics_snapshot_service.get_snapshot_series(
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
                            "department_id": "hr",
                            "source": f"hr_snapshot_{scope}",
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
        pdi_unit_values = {
            item.branch_code: item.active_pdi_pct
            for item in snapshot.branches
        }

        items = [
            {
                "department_id": "hr",
                "indicator_id": "hr-absenteeism",
                "value": self._resolve_indicator_value(
                    unit_values=absenteeism_unit_values,
                    branch=branch,
                ),
                "source": "portal_rh_absenteeism",
                "unit_values": absenteeism_unit_values,
            },
            {
                "department_id": "hr",
                "indicator_id": "hr-turnover",
                "value": self._resolve_indicator_value(
                    unit_values=turnover_unit_values,
                    branch=branch,
                ),
                "source": "portal_rh_turnover",
                "unit_values": turnover_unit_values,
            },
            {
                "department_id": "hr",
                "indicator_id": "hr-training-hours",
                "value": self._resolve_indicator_value(
                    unit_values=training_unit_values,
                    branch=branch,
                ),
                "source": "portal_rh_training",
                "unit_values": training_unit_values,
            },
        ]

        if snapshot.internal_satisfaction_pct is not None:
            items.append(
                {
                    "department_id": "hr",
                    "indicator_id": "hr-satisfaction",
                    "value": float(snapshot.internal_satisfaction_pct),
                    "source": "portal_rh_satisfaction",
                    "unit_values": {
                        "consolidated": float(snapshot.internal_satisfaction_pct)
                    },
                }
            )

        if snapshot.active_pdi_pct is not None:
            items.append(
                {
                    "department_id": "hr",
                    "indicator_id": "hr-pdi",
                    "value": self._resolve_indicator_value(
                        unit_values=pdi_unit_values,
                        branch=branch,
                    ),
                    "source": "portal_rh_pdi",
                    "unit_values": pdi_unit_values,
                }
            )

        return {
            "items": items,
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

        values = [float(value) for value in unit_values.values() if value is not None]
        if not values:
            return None

        return round(sum(values) / len(values), 2)