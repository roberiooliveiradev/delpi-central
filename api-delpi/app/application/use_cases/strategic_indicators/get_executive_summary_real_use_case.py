from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
)
from app.application.dto.strategic_indicators.get_executive_summary_real_request import (
    GetExecutiveSummaryRealRequest,
)
from app.application.use_cases.strategic_indicators.period_resolution import (
    previous_period,
    resolve_period,
)
from app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
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


class GetStrategicIndicatorsExecutiveSummaryRealUseCase:
    def __init__(
        self,
        *,
        departments_catalog_repository: StrategicIndicatorsDepartmentsCatalogRepositoryPort,
        indicators_catalog_repository: StrategicIndicatorsIndicatorsCatalogRepositoryPort,
        measurements_port: StrategicIndicatorsIndicatorMeasurementsPort,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._departments_catalog_repository = departments_catalog_repository
        self._indicators_catalog_repository = indicators_catalog_repository
        self._measurements_port = measurements_port
        self._alerts_summary_port = alerts_summary_port
        self._calculator = calculator

    def execute(
        self,
        request: GetExecutiveSummaryRealRequest,
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
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()
        goals_by_department = (
            self._departments_catalog_repository.get_department_goal_summary()
        )

        current_measurements, measurement_errors = (
            self._measurements_port.get_indicator_measurements(
                start_date=current_period.start_date,
                end_date=current_period.end_date,
            )
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

        previous_departments_by_id = {
            item.department_id: item for item in previous_departments
        }

        igd, igd_exact, classification = self._calculator.calculate_igd(
            current_departments
        )
        _previous_igd, previous_igd_exact, _ = self._calculator.calculate_igd(
            previous_departments
        )

        variation = self._calculator.calculate_variation(
            igd_exact,
            previous_igd_exact,
            decimals=3,
        )

        return {
            "competence": current_period.competence,
            "igd": igd,
            "igd_exact": igd_exact,
            "classification": classification,
            "variation": {
                "value": round(float(variation["value"]), 1),
                "direction": variation["direction"],
                "vs_label": "vs período anterior",
            },
            "departments": [
                self._map_department(
                    current=item,
                    previous=previous_departments_by_id.get(item.department_id),
                    goals_by_department=goals_by_department,
                )
                for item in current_departments
            ],
            "alerts_summary": self._alerts_summary_port.get_alerts_summary(
                departments=current_departments,
                measurement_errors=measurement_errors,
            ),
            "errors": measurement_errors,
            "partial_success": len(measurement_errors) > 0,
        }

    def _map_department(
        self,
        *,
        current: StrategicDepartmentCalculatedValue,
        previous: StrategicDepartmentCalculatedValue | None,
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