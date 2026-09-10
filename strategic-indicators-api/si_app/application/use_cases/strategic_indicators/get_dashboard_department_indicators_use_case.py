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
        goals = self._calculator.resolve_goals_payload_for_calculated(
            calculated=indicator,
            catalog_item=catalog_item,
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )
        presentation_goal_value = self._presentation_goal_value(
            indicator=indicator,
            catalog_item=catalog_item,
        )
        goal_mode = getattr(indicator, "goal_mode", "standard")
        reference_goal = self._calculator.resolve_reference_goal(
            goal_value=presentation_goal_value,
            goal_periodicity=indicator.goal_periodicity or "monthly",
            goal_mode=goal_mode,
            monthly_targets=getattr(indicator, "monthly_targets", None) or [],
            start_date=start_date,
            end_date=end_date,
            competence=competence,
        )
        comparable_goal = None
        if isinstance(goals, dict):
            for key in ("consolidated", "01", "02"):
                if goals.get(key) is not None:
                    try:
                        comparable_goal = float(goals[key])
                        break
                    except (TypeError, ValueError):
                        continue
            if comparable_goal is None:
                for value in goals.values():
                    try:
                        if value is not None:
                            comparable_goal = float(value)
                            break
                    except (TypeError, ValueError):
                        continue

        period_flags = self._calculator.resolve_goal_period_flags(
            start_date=start_date,
            end_date=end_date,
            competence=competence,
            value_unit=getattr(indicator, "value_unit", None),
            indicator_id=indicator.indicator_id,
        )

        return {
            "indicator_id": indicator.indicator_id,
            "name": indicator.indicator_name,
            "weight_pct": indicator.weight_pct,
            "goal_label": indicator.goal_label,
            "goal_value": presentation_goal_value,
            "comparable_goal": comparable_goal,
            "reference_goal": reference_goal,
            "goal_periodicity": indicator.goal_periodicity,
            "goal_mode": goal_mode,
            "goal_aggregation": period_flags.get("goal_aggregation"),
            "goal_period_kind": period_flags.get("goal_period_kind"),
            "goal_period_partial": period_flags.get("goal_period_partial"),
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
            "goals": goals,
            "classification": indicator.classification,
            "value_unit": getattr(indicator, "value_unit", None),
            "value_prefix": getattr(indicator, "value_prefix", None),
            "value_suffix": getattr(indicator, "value_suffix", None),
            "value_decimals": int(getattr(indicator, "value_decimals", 2) or 2),
        }

    def _presentation_goal_value(self, *, indicator, catalog_item=None) -> float | None:
        """Cadastral Meta mês for UI: rollup 01+02 when branch goals exist."""
        from si_app.shared.consolidated_value_aggregation import (
            aggregate_branch_goal_values,
        )
        from si_app.shared.goal_scope import BRANCH_UNIT_CODES

        branch_goals = None
        if catalog_item is not None:
            branch_goals = getattr(catalog_item, "branch_goals", None)
        if not branch_goals:
            branch_goals = getattr(indicator, "branch_goals", None)
        if isinstance(branch_goals, dict) and branch_goals:
            raw_values = [
                float(branch_goals[code]["goal_value"])
                for code in BRANCH_UNIT_CODES
                if branch_goals.get(code) is not None
                and branch_goals[code].get("goal_value") is not None
            ]
            if len(raw_values) >= 2:
                rolled = aggregate_branch_goal_values(
                    raw_values,
                    branch_value_aggregation=(
                        getattr(catalog_item, "branch_value_aggregation", None)
                        if catalog_item is not None
                        else getattr(indicator, "branch_value_aggregation", None)
                    ),
                    value_unit=(
                        getattr(catalog_item, "value_unit", None)
                        if catalog_item is not None
                        else getattr(indicator, "value_unit", None)
                    ),
                )
                if rolled is not None:
                    return float(rolled)
            if len(raw_values) == 1:
                return raw_values[0]
        try:
            return float(indicator.goal_value) if indicator.goal_value is not None else None
        except (TypeError, ValueError):
            return None
