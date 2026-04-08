from __future__ import annotations

from dataclasses import dataclass

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
        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        department_catalog = next(
            (item for item in departments_catalog if item.department_id == request.department_id),
            None,
        )

        if department_catalog is None:
            raise DepartmentNotFoundError(
                f"Departamento '{request.department_id}' não encontrado."
            )

        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        measurements, errors = self._measurements_port.get_indicator_measurements(
            start_date=request.start_date,
            end_date=request.end_date,
            department_id=request.department_id,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=[department_catalog],
            indicators_catalog=indicators_catalog,
            measurements=measurements,
        )

        if not calculated_departments:
            raise DepartmentNotFoundError(
                f"Departamento '{request.department_id}' não encontrado."
            )

        department = calculated_departments[0]

        return {
            "id": department.department_id,
            "name": department.department_name,
            "short_name": department.short_name,
            "weight_pct": department.weight_pct,
            "score": department.score,
            "classification": department.classification,
            "contribution": department.contribution,
            "aggregation_mode": department.aggregation_mode,
            "strategic_summary": department.strategic_summary,
            "variation": {
                "value": 0.0,
                "direction": department.trend,
            },
            "units": self._build_units(department),
            "indicators": [
                {
                    "id": indicator.indicator_id,
                    "name": indicator.indicator_name,
                    "weight_pct": indicator.weight_pct,
                    "goal_2026": indicator.goal_2026,
                    "strategic_description": indicator.strategic_description,
                    "scope_type": indicator.scope_type,
                    "realized": indicator.unit_values or {"consolidated": indicator.value},
                    "score": indicator.score,
                    "gap": indicator.gap,
                    "trend": indicator.trend,
                }
                for indicator in department.indicators
            ],
            "errors": errors,
            "partial_success": len(errors) > 0,
        }

    def _build_units(self, department) -> list[dict]:
        unit_scores: dict[str, list[float]] = {}

        for indicator in department.indicators:
            if not indicator.unit_values:
                continue

            for unit_id, raw_value in indicator.unit_values.items():
                unit_score = self._calculator._calculate_score(  # temporary reuse
                    indicator_id=indicator.indicator_id,
                    goal_text=indicator.goal_2026,
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
                    "classification": self._calculator._classify_score(avg_score),
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