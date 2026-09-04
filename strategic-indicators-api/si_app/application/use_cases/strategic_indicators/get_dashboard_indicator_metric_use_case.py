from __future__ import annotations

from typing import Literal

from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_service import (
    StrategicIndicatorsSnapshotService,
)
from si_app.domain.services.consolidated_branch_goal_rollup_service import (
    ConsolidatedBranchGoalRollupService,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.shared.goal_scope import BRANCH_UNIT_CODES, normalize_goal_scope_branch
from si_app.shared.numeric_parsing import to_optional_float

MetricKind = Literal["realized", "meta"]


class GetDashboardIndicatorMetricUseCase:
    """Meta ou realizado de um indicador SI (integração dashboards / TV)."""

    def __init__(
        self,
        *,
        snapshot_service: StrategicIndicatorsSnapshotService,
        calculator: StrategicIndicatorsCalculator,
    ) -> None:
        self._snapshot_service = snapshot_service
        self._calculator = calculator
        self._branch_goal_rollup = ConsolidatedBranchGoalRollupService(
            reference_resolver=calculator,
        )

    def execute(
        self,
        *,
        indicator_id: str,
        kind: MetricKind,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict | None:
        normalized_id = (indicator_id or "").strip()
        if not normalized_id:
            return None

        view_branch = normalize_goal_scope_branch(branch)
        snapshot = self._snapshot_service.get_current_and_previous_snapshot(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=None,
            branch=branch,
        )
        catalog_by_id = {
            item.indicator_id: item
            for item in snapshot.catalog.indicators_catalog
        }
        catalog_item = catalog_by_id.get(normalized_id)
        period = snapshot.current.period

        calculated = None
        for department in snapshot.current.calculated_departments:
            for indicator in department.indicators:
                if indicator.indicator_id == normalized_id:
                    calculated = indicator
                    break
            if calculated is not None:
                break

        if calculated is None and catalog_item is None:
            return None

        source_key = None
        if catalog_item is not None:
            source_key = getattr(catalog_item, "source_key", None)
        if not source_key and calculated is not None:
            source_key = getattr(calculated, "source", None)

        name = (
            calculated.indicator_name
            if calculated is not None
            else getattr(catalog_item, "indicator_name", normalized_id)
        )
        department_id = (
            calculated.department_id
            if calculated is not None
            else getattr(catalog_item, "department_id", None)
        )
        formatting_source = calculated if calculated is not None else catalog_item

        base = {
            "indicator_id": normalized_id,
            "source_key": source_key,
            "name": name,
            "department_id": department_id,
            "value_unit": getattr(formatting_source, "value_unit", None),
            "value_prefix": getattr(formatting_source, "value_prefix", None),
            "value_suffix": getattr(formatting_source, "value_suffix", None),
            "value_decimals": int(
                getattr(formatting_source, "value_decimals", 2) or 2
            ),
            "partial_success": len(snapshot.current.measurement_errors) > 0,
        }

        if kind == "realized":
            value = calculated.value if calculated is not None else None
            realized = (
                self._calculator.build_realized_payload(
                    unit_values=calculated.unit_values,
                    value=calculated.value,
                    department_id=calculated.department_id,
                )
                if calculated is not None
                else {}
            )
            return {
                **base,
                "value": value,
                "has_value": self._calculator.indicator_has_value(value),
                "realized": realized,
                "score": calculated.score if calculated is not None else None,
            }

        goal_value = (
            calculated.goal_value
            if calculated is not None
            else getattr(catalog_item, "goal_value", None)
        )
        goal_label = (
            calculated.goal_label
            if calculated is not None
            else getattr(catalog_item, "goal_label", None)
        )
        goals: dict = {}
        comparable_goal = None
        reference_goal = None
        value_unit = getattr(formatting_source, "value_unit", None)
        indicator_id_for_goal = normalized_id

        if calculated is not None:
            goals = self._calculator.resolve_goals_payload_for_calculated(
                calculated=calculated,
                catalog_item=catalog_item,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )

        rolled = self._rollup_registered_goal_for_consolidated(
            catalog_item=catalog_item,
            calculated=calculated,
            period=period,
        )

        if view_branch in BRANCH_UNIT_CODES:
            comparable_goal = goals.get(view_branch) if goals else None
            branch_fields = self._registered_goal_fields_for_branch(
                catalog_item=catalog_item,
                calculated=calculated,
                branch_code=view_branch,
            )
            if branch_fields is not None:
                goal_value = branch_fields["goal_value"]
                reference_goal = self._calculator.resolve_reference_goal(
                    goal_value=to_optional_float(branch_fields["goal_value"]),
                    goal_periodicity=branch_fields["goal_periodicity"],
                    goal_mode=branch_fields["goal_mode"],
                    monthly_targets=branch_fields["monthly_targets"],
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                )
                if comparable_goal is None:
                    comparable_goal = self._comparable_from_registered_fields(
                        fields=branch_fields,
                        period=period,
                        value_unit=value_unit,
                        indicator_id=indicator_id_for_goal,
                    )
        else:
            # Consolidado: usa rollup 01+02 / goals.consolidated — não a filial primária.
            if rolled is not None:
                goal_value = rolled["goal_value"]
                reference_goal = self._calculator.resolve_reference_goal(
                    goal_value=to_optional_float(rolled.get("goal_value")),
                    goal_periodicity=rolled.get("goal_periodicity") or "monthly",
                    goal_mode=rolled.get("goal_mode") or "standard",
                    monthly_targets=rolled.get("monthly_targets") or [],
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                )
            # Preferir comparable do rollup (1× MTD na soma das refs) para
            # paridade com dashboard-goals; goals.consolidated pode divergir
            # por arredondamento da soma dos comparables por filial.
            if rolled is not None:
                comparable_goal = self._comparable_from_registered_fields(
                    fields=rolled,
                    period=period,
                    value_unit=value_unit,
                    indicator_id=indicator_id_for_goal,
                )
            if comparable_goal is None and goals:
                comparable_goal = goals.get("consolidated")

        # Sem rollup de filiais: referência/comparable a partir do cadastro do indicador.
        if rolled is None and reference_goal is None and calculated is not None:
            goal_mode = getattr(calculated, "goal_mode", "standard") or "standard"
            goal_periodicity = calculated.goal_periodicity or "monthly"
            monthly_targets = getattr(calculated, "monthly_targets", None) or []
            reference_goal = self._calculator.resolve_reference_goal(
                goal_value=float(calculated.goal_value)
                if calculated.goal_value is not None
                else None,
                goal_periodicity=goal_periodicity,
                goal_mode=goal_mode,
                monthly_targets=monthly_targets,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )
            if comparable_goal is None and (
                calculated.goal_value is not None
                or str(goal_mode).strip().lower() == "monthly_curve"
            ):
                comparable_goal = self._calculator.calculate_comparable_goal(
                    goal_value=float(calculated.goal_value or 0),
                    goal_periodicity=goal_periodicity,
                    goal_mode=goal_mode,
                    monthly_targets=monthly_targets,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                    value_unit=value_unit,
                    indicator_id=indicator_id_for_goal,
                )
        elif rolled is None and reference_goal is None and catalog_item is not None:
            catalog_mode = getattr(catalog_item, "goal_mode", "standard") or "standard"
            catalog_periodicity = getattr(catalog_item, "goal_periodicity", None) or "monthly"
            catalog_targets = getattr(catalog_item, "monthly_targets", None) or []
            reference_goal = self._calculator.resolve_reference_goal(
                goal_value=to_optional_float(goal_value),
                goal_periodicity=catalog_periodicity,
                goal_mode=catalog_mode,
                monthly_targets=catalog_targets,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )

        if comparable_goal is None and goals:
            for key in ("consolidated", "01", "02"):
                if goals.get(key) is not None:
                    comparable_goal = goals[key]
                    break
            if comparable_goal is None:
                comparable_goal = next(
                    (v for v in goals.values() if v is not None),
                    None,
                )

        return {
            **base,
            "value": comparable_goal,
            "comparable_goal": comparable_goal,
            "goal_value": goal_value,
            "reference_goal": reference_goal,
            "goal_label": goal_label,
            "goals": goals,
            "has_value": comparable_goal is not None,
        }

    def _rollup_registered_goal_for_consolidated(
        self,
        *,
        catalog_item,
        calculated,
        period,
    ) -> dict | None:
        branch_goals = getattr(catalog_item, "branch_goals", None) if catalog_item else None
        if not branch_goals:
            return None
        indicator = {
            "value_unit": getattr(calculated, "value_unit", None)
            if calculated is not None
            else getattr(catalog_item, "value_unit", None),
            "branch_value_aggregation": getattr(calculated, "branch_value_aggregation", None)
            if calculated is not None
            else getattr(catalog_item, "branch_value_aggregation", None),
        }
        return self._branch_goal_rollup.rollup_branch_goals(
            indicator=indicator,
            branch_goals_by_code=dict(branch_goals),
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
        )

    def _registered_goal_fields_for_branch(
        self,
        *,
        catalog_item,
        calculated,
        branch_code: str,
    ) -> dict | None:
        branch_goals = getattr(catalog_item, "branch_goals", None) if catalog_item else None
        if branch_goals and branch_goals.get(branch_code):
            branch_goal = branch_goals[branch_code]
            return {
                "goal_value": branch_goal.get("goal_value"),
                "goal_periodicity": branch_goal.get("goal_periodicity")
                or getattr(catalog_item, "goal_periodicity", None)
                or "monthly",
                "goal_mode": branch_goal.get("goal_mode")
                or getattr(catalog_item, "goal_mode", "standard")
                or "standard",
                "monthly_targets": branch_goal.get("monthly_targets")
                or getattr(catalog_item, "monthly_targets", None)
                or [],
            }
        if calculated is None:
            return None
        return {
            "goal_value": calculated.goal_value,
            "goal_periodicity": calculated.goal_periodicity or "monthly",
            "goal_mode": getattr(calculated, "goal_mode", "standard") or "standard",
            "monthly_targets": getattr(calculated, "monthly_targets", None) or [],
        }

    def _comparable_from_registered_fields(
        self,
        *,
        fields: dict,
        period,
        value_unit: str | None,
        indicator_id: str | None,
    ) -> float | None:
        goal_value = fields.get("goal_value")
        goal_mode = fields.get("goal_mode") or "standard"
        if goal_value is None and str(goal_mode).strip().lower() != "monthly_curve":
            return None
        return self._calculator.calculate_comparable_goal(
            goal_value=float(goal_value or 0),
            goal_periodicity=fields.get("goal_periodicity") or "monthly",
            goal_mode=goal_mode,
            monthly_targets=fields.get("monthly_targets") or [],
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            value_unit=value_unit,
            indicator_id=indicator_id,
        )
