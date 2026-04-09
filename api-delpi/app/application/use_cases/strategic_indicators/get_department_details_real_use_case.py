from __future__ import annotations

from dataclasses import dataclass

from app.application.use_cases.strategic_indicators.period_resolution import (
    previous_period,
    resolve_period,
)
from app.domain.ports.strategic_indicators.departments_catalog_repository_port import (
    StrategicIndicatorsDepartmentsCatalogRepositoryPort,
)
from app.domain.ports.strategic_indicators.indicator_measurements_port import (
    StrategicIndicatorsIndicatorMeasurementsPort,
)
from app.domain.ports.strategic_indicators.indicators_catalog_repository_port import (
    StrategicIndicatorsIndicatorsCatalogRepositoryPort,
)
from app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class DepartmentNotFoundError(ValueError):
    pass


@dataclass
class GetStrategicIndicatorsDepartmentDetailsRealRequest:
    department_id: str
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsDepartmentDetailsRealUseCase:
    def __init__(
        self,
        *,
        departments_catalog_repository: StrategicIndicatorsDepartmentsCatalogRepositoryPort,
        indicators_catalog_repository: StrategicIndicatorsIndicatorsCatalogRepositoryPort,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._indicators_catalog_repository = indicators_catalog_repository
        self._measurements_port = measurements_port
        self._calculator = calculator

    def execute(
        self,
        request: GetStrategicIndicatorsDepartmentDetailsRealRequest,
    ) -> dict:
        current_period = resolve_period(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        prev_period = previous_period(current_period)

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        department_catalog = next(
            (
                item
                for item in departments_catalog
                if item.department_id == request.department_id
            ),
            None,
        )

        if department_catalog is None:
            raise DepartmentNotFoundError(
                f"Departamento '{request.department_id}' não encontrado."
            )

        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        current_measurements, errors = self._measurements_port.get_indicator_measurements(
            start_date=current_period.start_date,
            end_date=current_period.end_date,
            department_id=request.department_id,
        )
        previous_measurements, _ = self._measurements_port.get_indicator_measurements(
            start_date=prev_period.start_date,
            end_date=prev_period.end_date,
            department_id=request.department_id,
        )

        current_departments = self._calculator.calculate_departments(
            departments_catalog=[department_catalog],
            indicators_catalog=indicators_catalog,
            measurements=current_measurements,
            start_date=current_period.start_date,
            end_date=current_period.end_date,
            competence=current_period.competence,
        )
        previous_departments = self._calculator.calculate_departments(
            departments_catalog=[department_catalog],
            indicators_catalog=indicators_catalog,
            measurements=previous_measurements,
            start_date=prev_period.start_date,
            end_date=prev_period.end_date,
            competence=prev_period.competence,
        )

        if not current_departments:
            raise DepartmentNotFoundError(
                f"Departamento '{request.department_id}' não encontrado."
            )

        current_department = current_departments[0]
        previous_department = previous_departments[0] if previous_departments else None

        previous_indicators_by_id = {
            item.indicator_id: item
            for item in (previous_department.indicators if previous_department else [])
        }

        previous_score = (
            previous_department.score if previous_department is not None else current_department.score
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
                start_date=current_period.start_date,
                end_date=current_period.end_date,
                competence=current_period.competence,
            ),
            "indicators": [
                self._map_indicator(
                    current=indicator,
                    previous=previous_indicators_by_id.get(indicator.indicator_id),
                )
                for indicator in current_department.indicators
            ],
            "errors": errors,
            "partial_success": len(errors) > 0,
        }

    def _map_indicator(self, *, current, previous) -> dict:
        previous_score = previous.score if previous is not None else current.score
        trend = self._calculator.resolve_trend_direction(
            current=current.score,
            previous=previous_score,
        )

        return {
            "id": current.indicator_id,
            "name": current.indicator_name,
            "weight_pct": current.weight_pct,
            "goal_label": current.goal_label,
            "goal_value": current.goal_value,
            "goal_periodicity": current.goal_periodicity,
            "strategic_description": current.strategic_description,
            "scope_type": current.scope_type,
            "realized": current.unit_values or {"consolidated": current.value},
            "score": current.score,
            "gap": current.gap,
            "trend": trend,
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

        for indicator in department.indicators:
            if not indicator.unit_values:
                continue

            comparable_goal = self._calculator.calculate_comparable_goal(
                goal_value=indicator.goal_value,
                goal_periodicity=indicator.goal_periodicity,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            )

            for unit_id, raw_value in indicator.unit_values.items():
                unit_score = self._calculator.calculate_indicator_score(
                    indicator_id=indicator.indicator_id,
                    comparable_goal=comparable_goal,
                    value=float(raw_value),
                )
                unit_scores.setdefault(unit_id, []).append(unit_score)

        units: list[dict] = []
        for unit_id, scores in unit_scores.items():
            if not scores:
                continue

            avg_score = round(sum(scores) / len(scores), 3)
            units.append(
                {
                    "unit_id": unit_id,
                    "unit_name": self._resolve_unit_name(unit_id),
                    "score": avg_score,
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