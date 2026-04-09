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


@dataclass
class GetStrategicIndicatorsDepartmentsRealRequest:
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsDepartmentsRealUseCase:
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
        request: GetStrategicIndicatorsDepartmentsRealRequest | None = None,
    ) -> dict:
        request = request or GetStrategicIndicatorsDepartmentsRealRequest()
        current_period = resolve_period(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        prev_period = previous_period(current_period)

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        current_measurements, errors = self._measurements_port.get_indicator_measurements(
            start_date=current_period.start_date,
            end_date=current_period.end_date,
        )
        previous_measurements, _ = self._measurements_port.get_indicator_measurements(
            start_date=prev_period.start_date,
            end_date=prev_period.end_date,
        )

        current_departments = self._calculator.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            measurements=current_measurements,
            start_date=current_period.start_date,
            end_date=current_period.end_date,
            competence=current_period.competence,
        )
        previous_departments = self._calculator.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            measurements=previous_measurements,
            start_date=prev_period.start_date,
            end_date=prev_period.end_date,
            competence=prev_period.competence,
        )

        previous_by_id = {item.department_id: item for item in previous_departments}

        return {
            "items": [
                self._map_department(
                    current=item,
                    previous=previous_by_id.get(item.department_id),
                )
                for item in current_departments
            ],
            "errors": errors,
            "partial_success": len(errors) > 0,
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