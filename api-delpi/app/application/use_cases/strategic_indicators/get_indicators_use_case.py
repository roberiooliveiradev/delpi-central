from __future__ import annotations

from app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
    IndicatorFetchErrorResponse,
    IndicatorItemResponse,
)
from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)


class GetStrategicIndicatorsUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
    ) -> None:
        self._snapshot_service = snapshot_service

    def execute(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        competence: str | None = None,
    ) -> GetStrategicIndicatorsResponse:
        snapshot = self._snapshot_service.get_period_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
        )

        departments_by_id = {
            item.department_id: item
            for item in snapshot.calculated_departments
        }

        return GetStrategicIndicatorsResponse(
            items=[
                IndicatorItemResponse(
                    department_id=item.department_id,
                    department_name=departments_by_id[item.department_id].department_name,
                    indicator_id=item.indicator_id,
                    indicator_name=item.indicator_name,
                    weight_pct=int(item.weight_pct),
                    goal_label=item.goal_label,
                    goal_value=float(item.goal_value),
                    goal_periodicity=item.goal_periodicity,
                    scope_type=item.scope_type,
                    value=float(item.value),
                    score=float(item.score),
                    gap=float(item.gap),
                    trend=item.trend,
                    classification=item.classification,
                    source=item.source,
                )
                for item in snapshot.calculated_indicators
            ],
            errors=[
                IndicatorFetchErrorResponse(
                    department_id=error["department_id"],
                    source=error["source"],
                    message=error["message"],
                )
                for error in snapshot.measurement_errors
            ],
        )