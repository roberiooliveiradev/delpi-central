from __future__ import annotations

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class GetDashboardDepartmentIndicatorsUseCase:
    """IDD do departamento + indicadores com metas e realizado (integração dashboards)."""

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
        *,
        department_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict | None:
        normalized_id = (department_id or "").strip()
        if not normalized_id:
            return None

        # Mesma base materializada das telas SI (escopo global) para metas/realizado.
        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=None,
            branch=branch,
        )
        department = next(
            (
                item
                for item in snapshot.current.calculated_departments
                if item.department_id == normalized_id
            ),
            None,
        )
        if department is None:
            return None

        catalog_by_id = {
            item.indicator_id: item
            for item in snapshot.catalog.indicators_catalog
        }
        period = snapshot.current.period

        return {
            "department_id": department.department_id,
            "department_name": department.department_name,
            "short_name": department.short_name,
            "idd": department.score,
            "score": department.score,
            "classification": department.classification,
            "contribution": department.contribution,
            "aggregation_mode": department.aggregation_mode,
            "indicators": [
                self.map_indicator(
                    indicator=indicator,
                    catalog_item=catalog_by_id.get(indicator.indicator_id),
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                )
                for indicator in department.indicators
            ],
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

    def map_indicator(
        self,
        *,
        indicator,
        catalog_item=None,
        start_date: str | None,
        end_date: str | None,
        competence: str | None,
    ) -> dict:
        return {
            "indicator_id": indicator.indicator_id,
            "name": indicator.indicator_name,
            "weight_pct": indicator.weight_pct,
            "goal_label": indicator.goal_label,
            "goal_value": indicator.goal_value,
            "goal_periodicity": indicator.goal_periodicity,
            "goal_mode": getattr(indicator, "goal_mode", "standard"),
            "performance_direction": getattr(
                indicator,
                "performance_direction",
                "higher_is_better",
            ),
            "value": indicator.value,
            "has_value": self._calculator.indicator_has_value(indicator.value),
            "score": indicator.score,
            "gap": indicator.gap,
            "realized": self._calculator.build_realized_payload(
                unit_values=indicator.unit_values,
                value=indicator.value,
                department_id=indicator.department_id,
            ),
            "goals": self._calculator.resolve_goals_payload_for_calculated(
                calculated=indicator,
                catalog_item=catalog_item,
                start_date=start_date,
                end_date=end_date,
                competence=competence,
            ),
            "classification": indicator.classification,
            "value_unit": getattr(indicator, "value_unit", None),
            "value_prefix": getattr(indicator, "value_prefix", None),
            "value_suffix": getattr(indicator, "value_suffix", None),
            "value_decimals": int(getattr(indicator, "value_decimals", 2) or 2),
        }
