from __future__ import annotations

from dataclasses import dataclass

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class DepartmentNotFoundError(ValueError):
    pass


@dataclass
class GetStrategicIndicatorsDepartmentDetailsRealRequest:
    department_id: str
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsDepartmentDetailsRealUseCase:
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
        request: GetStrategicIndicatorsDepartmentDetailsRealRequest,
    ) -> dict:
        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            department_id=request.department_id,
            branch=request.branch,
        )

        if not snapshot.current.calculated_departments:
            raise DepartmentNotFoundError(
                f"Departamento '{request.department_id}' não encontrado."
            )

        current_department = snapshot.current.calculated_departments[0]
        previous_department = (
            snapshot.previous.calculated_departments[0]
            if snapshot.previous.calculated_departments
            else None
        )

        previous_indicators_by_id = {
            item.indicator_id: item
            for item in (previous_department.indicators if previous_department else [])
        }

        previous_score = (
            previous_department.score
            if previous_department is not None
            else current_department.score
        )
        department_variation = self._calculator.calculate_variation(
            current_department.score,
            previous_score,
            decimals=3,
        )

        return {
            "id": current_department.department_id,
            "name": current_department.department_name,
            "short_name": current_department.short_name,
            "weight_pct": current_department.weight_pct,
            "score": current_department.score,
            "classification": current_department.classification,
            "contribution": current_department.contribution,
            "aggregation_mode": current_department.aggregation_mode,
            "strategic_summary": current_department.strategic_summary,
            "variation": {
                "value": float(department_variation["value"]),
                "direction": department_variation["direction"],
            },
            "units": self._build_units(
                current_department,
                start_date=snapshot.current.period.start_date,
                end_date=snapshot.current.period.end_date,
                competence=snapshot.current.period.competence,
            ),
            "indicators": [
                self._map_indicator(
                    current=indicator,
                    previous=previous_indicators_by_id.get(indicator.indicator_id),
                )
                for indicator in current_department.indicators
            ],
            "errors": snapshot.current.measurement_errors,
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

    def _map_indicator(self, *, current, previous) -> dict:
        previous_score = previous.score if previous is not None else current.score
        trend = (
            "stable"
            if current.score is None
            else self._calculator.resolve_trend_direction(
                current=current.score,
                previous=previous_score,
            )
        )

        return {
            "id": current.indicator_id,
            "name": current.indicator_name,
            "weight_pct": current.weight_pct,
            "goal_label": current.goal_label,
            "goal_value": current.goal_value,
            "goal_periodicity": current.goal_periodicity,
            "goal_mode": getattr(current, "goal_mode", "standard"),
            "monthly_targets": getattr(current, "monthly_targets", []) or [],
            "strategic_description": current.strategic_description,
            "scope_type": current.scope_type,
            "performance_direction": getattr(
                current,
                "performance_direction",
                "higher_is_better",
            ),
            "realized": self._calculator.build_realized_payload(
                unit_values=current.unit_values,
                value=current.value,
                department_id=current.department_id,
            ),
            "has_value": self._calculator.indicator_has_value(current.value),
            "classification": current.classification,
            "score": current.score,
            "gap": current.gap,
            "gaps": self._calculator.build_gaps_payload(
                unit_gaps=current.unit_gaps,
                gap=current.gap,
                department_id=current.department_id,
            ),
            "trend": trend,
            "value_unit": getattr(current, "value_unit", None),
            "value_prefix": getattr(current, "value_prefix", None),
            "value_suffix": getattr(current, "value_suffix", None),
            "value_decimals": int(getattr(current, "value_decimals", 2) or 2),
        }

    def _build_units(
        self,
        department,
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> list[dict]:
        unit_scores: dict[str, list[float]] = {}
        unit_ids: set[str] = set()

        for indicator in department.indicators:
            if not indicator.unit_values:
                continue

            comparable_goal = self._calculator.calculate_comparable_goal(
                goal_value=indicator.goal_value,
                goal_periodicity=indicator.goal_periodicity,
                goal_mode=getattr(indicator, "goal_mode", "standard"),
                monthly_targets=getattr(indicator, "monthly_targets", None),
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

            for unit_id, raw_value in indicator.unit_values.items():
                unit_ids.add(unit_id)

                if raw_value is None:
                    continue

                unit_score = self._calculator.calculate_indicator_score(
                    performance_direction=getattr(
                        indicator,
                        "performance_direction",
                        "higher_is_better",
                    ),
                    comparable_goal=comparable_goal,
                    value=float(raw_value),
                )
                unit_scores.setdefault(unit_id, []).append(unit_score)

        units: list[dict] = []
        for unit_id in sorted(unit_ids):
            scores = unit_scores.get(unit_id, [])
            if not scores:
                units.append(
                    {
                        "unit_id": unit_id,
                        "unit_name": self._resolve_unit_name(unit_id),
                        "score": None,
                        "has_value": False,
                        "classification": self._calculator.MISSING_VALUE_CLASSIFICATION,
                    }
                )
                continue

            avg_score = round(sum(scores) / len(scores), 3)
            units.append(
                {
                    "unit_id": unit_id,
                    "unit_name": self._resolve_unit_name(unit_id),
                    "score": avg_score,
                    "has_value": True,
                    "classification": self._calculator.classify_score(avg_score),
                }
            )

        return units

    def _resolve_unit_name(self, unit_id: str) -> str:
        if unit_id == "matrix":
            return "Matriz"
        if unit_id == "branch":
            return "Filial"
        if unit_id == "consolidated":
            return "Consolidado"
        return unit_id