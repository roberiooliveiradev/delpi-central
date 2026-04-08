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

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        measurements, errors = self._measurements_port.get_indicator_measurements(
            start_date=request.start_date,
            end_date=request.end_date,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            start_date=request.start_date,
            end_date=request.end_date,
            competence=request.competence,
        )

        return {
            "items": [
                {
                    "id": item.department_id,
                    "name": item.department_name,
                    "short_name": item.short_name,
                    "weight_pct": item.weight_pct,
                    "score": item.score,
                    "classification": item.classification,
                    "contribution": item.contribution,
                    "aggregation_mode": item.aggregation_mode,
                    "strategic_summary": item.strategic_summary,
                    "variation": {
                        "value": 0.0,
                        "direction": item.trend,
                    },
                }
                for item in calculated_departments
            ],
            "errors": errors,
            "partial_success": len(errors) > 0,
        }