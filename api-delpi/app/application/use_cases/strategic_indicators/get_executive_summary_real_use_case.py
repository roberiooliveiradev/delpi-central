from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
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

from app.application.dto.strategic_indicators.get_executive_summary_real_request import GetExecutiveSummaryRealRequest


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
        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()
        goals_by_department = self._departments_catalog_repository.get_department_goal_summary()

        measurements, measurement_errors = self._measurements_port.get_indicator_measurements(
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

        igd, igd_exact, classification = self._calculator.calculate_igd(
            calculated_departments
        )

        return {
            "competence": request.competence or self._resolve_competence(
                request.start_date,
                request.end_date,
            ),
            "igd": igd,
            "igd_exact": igd_exact,
            "classification": classification,
            "variation": {
                "value": 0.0,
                "direction": "stable",
                "vs_label": "vs período anterior",
            },
            "departments": [
                self._map_department(item, goals_by_department)
                for item in calculated_departments
            ],
            "alerts_summary": self._alerts_summary_port.get_alerts_summary(
                departments=calculated_departments,
                measurement_errors=measurement_errors,
            ),
            "errors": measurement_errors,
            "partial_success": len(measurement_errors) > 0,
        }

    def _map_department(
        self,
        department: StrategicDepartmentCalculatedValue,
        goals_by_department: dict[str, str],
    ) -> dict:
        return {
            "id": department.department_id,
            "name": department.department_name,
            "short_name": department.short_name,
            "weight_pct": department.weight_pct,
            "score": department.score,
            "contribution": department.contribution,
            "trend": department.trend,
            "strategic_summary": department.strategic_summary,
            "key_indicators": [
                indicator.indicator_name for indicator in department.indicators[:3]
            ],
            "executive_goal": goals_by_department.get(department.department_id, ""),
        }

    def _resolve_competence(
        self,
        start_date: str | None,
        end_date: str | None,
    ) -> str:
        if end_date and len(end_date) >= 10:
            day, month, year = end_date.split("-")
            return f"{year}-{month}"
        if start_date and len(start_date) >= 10:
            day, month, year = start_date.split("-")
            return f"{year}-{month}"
        from datetime import date
        return date.today().strftime("%Y-%m")