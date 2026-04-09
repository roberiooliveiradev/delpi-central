from __future__ import annotations

from dataclasses import dataclass

from app.application.use_cases.strategic_indicators.period_resolution import (
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


@dataclass
class GetStrategicIndicatorsAlertsRealRequest:
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsAlertsRealUseCase:
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
        request: GetStrategicIndicatorsAlertsRealRequest,
    ) -> dict:
        period = resolve_period(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        departments_catalog = (
            self._departments_catalog_repository.list_departments_catalog()
        )
        indicators_catalog = self._indicators_catalog_repository.list_indicators_catalog()

        catalog_by_indicator_id = {
            item.indicator_id: item for item in indicators_catalog
        }

        measurements, measurement_errors = self._measurements_port.get_indicator_measurements(
            start_date=period.start_date,
            end_date=period.end_date,
        )

        calculated_departments = self._calculator.calculate_departments(
            departments_catalog=departments_catalog,
            indicators_catalog=indicators_catalog,
            measurements=measurements,
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

        executive_alerts = self._alerts_summary_port.get_alerts_summary(
            departments=calculated_departments,
            measurement_errors=measurement_errors,
        )

        department_alerts = self._build_department_alerts(calculated_departments)
        indicator_alerts = self._build_indicator_alerts(
            calculated_departments,
            catalog_by_indicator_id,
        )

        return {
            "competence": period.competence,
            "executive_alerts": executive_alerts,
            "department_alerts": department_alerts,
            "indicator_alerts": indicator_alerts,
            "errors": measurement_errors,
            "partial_success": len(measurement_errors) > 0,
        }

    def _build_department_alerts(self, departments) -> list[dict]:
        ordered = sorted(departments, key=lambda item: item.score)
        alerts: list[dict] = []

        for department in ordered[:5]:
            if department.score >= 8:
                continue

            severity = "high" if department.score < 7 else "medium"

            alerts.append(
                {
                    "department_id": department.department_id,
                    "department_name": department.department_name,
                    "severity": severity,
                    "score": department.score,
                    "classification": department.classification,
                    "contribution": department.contribution,
                    "message": (
                        f"{department.department_name} está com score "
                        f"{department.score:.1f} e exige acompanhamento."
                    ),
                }
            )

        return alerts

    def _build_indicator_alerts(
        self,
        departments,
        catalog_by_indicator_id: dict,
    ) -> list[dict]:
        candidates: list[dict] = []

        for department in departments:
            for indicator in department.indicators:
                if indicator.score >= 8:
                    continue

                severity = "high" if indicator.score < 7 else "medium"
                catalog_item = catalog_by_indicator_id.get(indicator.indicator_id)

                candidates.append(
                    {
                        "department_id": department.department_id,
                        "department_name": department.department_name,
                        "indicator_id": indicator.indicator_id,
                        "indicator_name": indicator.indicator_name,
                        "severity": severity,
                        "score": indicator.score,
                        "gap": indicator.gap,
                        "classification": indicator.classification,
                        "source": indicator.source,
                        "goal_label": catalog_item.goal_label if catalog_item else None,
                        "goal_value": catalog_item.goal_value if catalog_item else None,
                        "goal_periodicity": (
                            catalog_item.goal_periodicity if catalog_item else None
                        ),
                        "message": (
                            f"{indicator.indicator_name} está abaixo do esperado em "
                            f"{department.department_name}."
                        ),
                    }
                )

        candidates.sort(key=lambda item: item["score"])
        return candidates[:8]