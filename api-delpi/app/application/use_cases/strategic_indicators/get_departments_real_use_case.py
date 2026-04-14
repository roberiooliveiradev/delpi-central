from __future__ import annotations

from dataclasses import dataclass

from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


@dataclass
class GetStrategicIndicatorsDepartmentsRealRequest:
    department_id: str | None = None
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsDepartmentsRealUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._calculator = calculator

    def execute(
        self,
        request: GetStrategicIndicatorsDepartmentsRealRequest | None = None,
    ) -> dict:
        request = request or GetStrategicIndicatorsDepartmentsRealRequest()

        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            department_id=request.department_id,
            branch=request.branch,
        )

        previous_by_id = {
            item.department_id: item for item in snapshot.previous.calculated_departments
        }

        return {
            "items": [
                self._map_department(
                    current=item,
                    previous=previous_by_id.get(item.department_id),
                )
                for item in snapshot.current.calculated_departments
            ],
            "errors": snapshot.current.measurement_errors,
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

    def _map_department(self, *, current, previous) -> dict:
        previous_score = previous.score if previous is not None else current.score
        variation = self._calculator.calculate_variation(
            current.score,
            previous_score,
            decimals=3,
        )

        return {
            "id": current.department_id,
            "name": current.department_name,
            "short_name": current.short_name,
            "weight_pct": current.weight_pct,
            "score": current.score,
            "classification": current.classification,
            "contribution": current.contribution,
            "aggregation_mode": current.aggregation_mode,
            "strategic_summary": current.strategic_summary,
            "variation": {
                "value": float(variation["value"]),
                "direction": variation["direction"],
            },
        }