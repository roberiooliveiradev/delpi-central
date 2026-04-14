from __future__ import annotations

from app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class GetStrategicIndicatorsExecutiveSummaryRealUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._alerts_summary_port = alerts_summary_port
        self._calculator = calculator

    def execute(self, request) -> dict:
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

        variation = self._calculator.calculate_variation(
            snapshot.current.igd_exact,
            snapshot.previous.igd_exact,
            decimals=3,
        )

        return {
            "competence": snapshot.current.period.competence,
            "igd": snapshot.current.igd,
            "igd_exact": snapshot.current.igd_exact,
            "classification": snapshot.current.classification,
            "variation": {
                "value": round(float(variation["value"]), 1),
                "direction": variation["direction"],
                "vs_label": "vs período anterior",
            },
            "departments": [
                self._map_department(
                    current=item,
                    previous=previous_by_id.get(item.department_id),
                    goals_by_department=snapshot.catalog.goals_by_department,
                )
                for item in snapshot.current.calculated_departments
            ],
            "alerts_summary": self._alerts_summary_port.get_alerts_summary(
                departments=snapshot.current.calculated_departments,
                measurement_errors=snapshot.current.measurement_errors,
            ),
            "errors": snapshot.current.measurement_errors,
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

    def _map_department(
        self,
        *,
        current,
        previous,
        goals_by_department: dict[str, str],
    ) -> dict:
        previous_score = previous.score if previous is not None else current.score
        trend = self._calculator.resolve_trend_direction(
            current=current.score,
            previous=previous_score,
        )
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
            "contribution": current.contribution,
            "trend": trend,
            "strategic_summary": current.strategic_summary,
            "key_indicators": [
                indicator.indicator_name for indicator in current.indicators[:3]
            ],
            "executive_goal": goals_by_department.get(current.department_id, ""),
            "variation": {
                "value": float(variation["value"]),
                "direction": variation["direction"],
            },
        }