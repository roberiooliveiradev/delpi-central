from __future__ import annotations

from app.application.dto.strategic_indicators.get_indicators_response import (
    GetStrategicIndicatorsResponse,
    IndicatorFetchErrorResponse,
    IndicatorItemResponse,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
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


class GetStrategicIndicatorsUseCase:
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
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        competence: str | None = None,
    ) -> GetStrategicIndicatorsResponse:
        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        departments_by_id = {
            item.department_id: item for item in departments_catalog
        }

        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()
        measurements, raw_errors = self._measurements_port.get_indicator_measurements(
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
        )

        calculated_items = self._calculator.calculate_indicators(
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            department_id=department_id,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

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
                for item in calculated_items
            ],
            errors=[
                IndicatorFetchErrorResponse(
                    department_id=error["department_id"],
                    source=error["source"],
                    message=error["message"],
                )
                for error in raw_errors
            ],
        )