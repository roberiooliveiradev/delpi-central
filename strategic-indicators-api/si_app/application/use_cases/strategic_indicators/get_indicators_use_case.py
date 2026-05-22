from __future__ import annotations

from si_app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
    IndicatorFetchErrorResponse,
    IndicatorItemResponse,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class GetStrategicIndicatorsUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        calculator: StrategicIndicatorsCalculator | None = None,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._calculator = calculator or StrategicIndicatorsCalculator()

    def execute(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
    ) -> GetStrategicIndicatorsResponse:
        snapshot = self._snapshot_service.get_period_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            branch=branch,
        )

        return self.build_from_period_snapshot(snapshot)

    def build_from_period_snapshot(
        self,
        snapshot: StrategicIndicatorsPeriodSnapshot,
    ) -> GetStrategicIndicatorsResponse:
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
                    goal_value=float(item.goal_value) if item.goal_value is not None else 0.0,
                    goal_periodicity=item.goal_periodicity,
                    goal_mode=getattr(item, "goal_mode", "standard"),
                    monthly_targets=getattr(item, "monthly_targets", []) or [],
                    scope_type=item.scope_type,
                    performance_direction=getattr(
                        item,
                        "performance_direction",
                        "higher_is_better",
                    ),
                    value=item.value,
                    realized=self._calculator.build_realized_payload(
                        unit_values=item.unit_values,
                        value=item.value,
                        department_id=item.department_id,
                    ),
                    score=item.score,
                    gap=item.gap,
                    gaps=self._calculator.build_gaps_payload(
                        unit_gaps=item.unit_gaps,
                        gap=item.gap,
                        department_id=item.department_id,
                    ),
                    has_value=item.value is not None,
                    trend=item.trend,
                    classification=item.classification,
                    source=item.source,
                    value_unit=getattr(item, "value_unit", None),
                    value_prefix=getattr(item, "value_prefix", None),
                    value_suffix=getattr(item, "value_suffix", None),
                    value_decimals=int(getattr(item, "value_decimals", 2) or 2),
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