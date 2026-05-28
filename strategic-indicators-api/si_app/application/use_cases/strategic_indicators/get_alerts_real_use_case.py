from __future__ import annotations

from dataclasses import dataclass

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.domain.ports.strategic_indicators.alerts_summary_port import (
    StrategicIndicatorsAlertsSummaryPort,
)
from si_app.shared.indicator_scoring import indicator_has_score


@dataclass
class GetStrategicIndicatorsAlertsRealRequest:
    department_id: str | None = None
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None


class GetStrategicIndicatorsAlertsRealUseCase:
    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        alerts_summary_port: StrategicIndicatorsAlertsSummaryPort,
        calculator: StrategicIndicatorsCalculator | None = None,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._alerts_summary_port = alerts_summary_port
        self._calculator = calculator or StrategicIndicatorsCalculator()

    def execute(
        self,
        request: GetStrategicIndicatorsAlertsRealRequest,
    ) -> dict:
        comparative = self._snapshot_service.get_current_and_previous_snapshot(
            competence=request.competence,
            start_date=request.start_date,
            end_date=request.end_date,
            department_id=request.department_id,
            branch=request.branch,
        )

        current_snapshot = comparative.current
        previous_snapshot = comparative.previous

        catalog_by_indicator_id = {
            item.indicator_id: item
            for item in comparative.catalog.indicators_catalog
        }

        previous_departments_by_id = {
            item.department_id: item
            for item in previous_snapshot.calculated_departments
        }

        executive_alerts = self._alerts_summary_port.get_alerts_summary(
            departments=current_snapshot.calculated_departments,
            measurement_errors=current_snapshot.measurement_errors,
        )

        department_alerts = self._build_department_alerts(
            current_snapshot.calculated_departments,
            previous_departments_by_id=previous_departments_by_id,
        )

        indicator_alerts = self._build_indicator_alerts(
            current_snapshot.calculated_departments,
            catalog_by_indicator_id,
            start_date=current_snapshot.period.start_date,
            end_date=current_snapshot.period.end_date,
            competence=current_snapshot.period.competence,
        )

        return {
            "competence": current_snapshot.period.competence,
            "executive_alerts": executive_alerts,
            "department_alerts": department_alerts,
            "indicator_alerts": indicator_alerts,
            "errors": current_snapshot.measurement_errors,
            "partial_success": len(current_snapshot.measurement_errors) > 0,
        }

    def _build_department_alerts(
        self,
        departments,
        *,
        previous_departments_by_id: dict,
    ) -> list[dict]:
        ordered = sorted(departments, key=lambda item: item.score)
        alerts: list[dict] = []

        for department in ordered[:5]:
            if department.score >= 8:
                continue

            severity = "high" if department.score < 7 else "medium"

            previous_department = previous_departments_by_id.get(
                department.department_id,
            )

            previous_score = (
                previous_department.score
                if previous_department is not None
                else department.score
            )

            variation = round(float(department.score) - float(previous_score), 3)

            alerts.append(
                {
                    "department_id": department.department_id,
                    "department_name": department.department_name,
                    "severity": severity,
                    "score": department.score,
                    "previous_score": previous_score,
                    "variation": variation,
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
        *,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> list[dict]:
        candidates: list[dict] = []

        for department in departments:
            for indicator in department.indicators:
                if not indicator_has_score(indicator):
                    continue

                if indicator.score >= 8:
                    continue

                severity = "high" if indicator.score < 7 else "medium"
                catalog_item = catalog_by_indicator_id.get(indicator.indicator_id)

                goals = (
                    self._calculator.resolve_goals_payload_for_calculated(
                        calculated=indicator,
                        catalog_item=catalog_item,
                        start_date=start_date,
                        end_date=end_date,
                        competence=competence,
                    )
                    if catalog_item is not None
                    else {}
                )

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
                        "goal_mode": (
                            getattr(catalog_item, "goal_mode", "standard")
                            if catalog_item
                            else "standard"
                        ),
                        "monthly_targets": (
                            getattr(catalog_item, "monthly_targets", []) or []
                            if catalog_item
                            else []
                        ),
                        "goals": goals,
                        "performance_direction": (
                            getattr(
                                catalog_item,
                                "performance_direction",
                                "higher_is_better",
                            )
                            if catalog_item
                            else "higher_is_better"
                        ),
                        "value_unit": getattr(catalog_item, "value_unit", None)
                        if catalog_item
                        else None,
                        "value_prefix": getattr(catalog_item, "value_prefix", None)
                        if catalog_item
                        else None,
                        "value_suffix": getattr(catalog_item, "value_suffix", None)
                        if catalog_item
                        else None,
                        "value_decimals": int(getattr(catalog_item, "value_decimals", 2) or 2)
                        if catalog_item
                        else 2,
                        "message": (
                            f"{indicator.indicator_name} está abaixo do esperado em "
                            f"{department.department_name}."
                        ),
                    }
                )

        candidates.sort(key=lambda item: item["score"])
        return candidates[:8]