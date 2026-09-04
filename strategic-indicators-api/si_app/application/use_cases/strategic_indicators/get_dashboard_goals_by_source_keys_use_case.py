from __future__ import annotations

import logging

from si_app.application.services.strategic_indicators.period_resolution import (
    resolve_period,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_department_indicators_repository import (
    PostgresStrategicIndicatorsDepartmentIndicatorsRepository,
)
from si_app.application.services.strategic_indicators.commercial_dashboard_source_keys import (
    COMMERCIAL_ROL_SOURCE_KEY,
    expand_dashboard_source_keys,
    legacy_rol_branch_override,
)
from si_app.shared.goal_scope import (
    BRANCH_UNIT_CODES,
    format_goal_scope_label,
    normalize_goal_scope_branch,
    resolve_goal_scope_hint_for_view,
)
from si_app.shared.consolidated_value_aggregation import (
    aggregate_branch_goal_values,
    is_source_consolidated_mode,
    normalize_branch_value_aggregation,
)

logger = logging.getLogger(__name__)


class GetDashboardGoalsBySourceKeysUseCase:
    def __init__(
        self,
        *,
        indicators_repository: PostgresStrategicIndicatorsDepartmentIndicatorsRepository
        | None = None,
        goals_repository: StrategicIndicatorsIndicatorGoalsRepositoryPort | None = None,
        calculator: StrategicIndicatorsCalculator | None = None,
    ) -> None:
        self._indicators_repository = (
            indicators_repository or PostgresStrategicIndicatorsDepartmentIndicatorsRepository()
        )
        self._goals_repository = goals_repository
        self._calculator = calculator or StrategicIndicatorsCalculator()

    def execute(
        self,
        *,
        source_keys: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
    ) -> list[dict]:
        normalized_keys = [
            str(key).strip()
            for key in source_keys
            if key is not None and str(key).strip()
        ]
        if not normalized_keys:
            return []

        lookup_keys = expand_dashboard_source_keys(normalized_keys)

        if self._goals_repository is None:
            from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
                PostgresStrategicIndicatorsIndicatorGoalsRepository,
            )

            self._goals_repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()

        indicators = self._indicators_repository.list_active_indicators_by_source_keys(
            lookup_keys,
            department_id=department_id,
        )
        if not indicators:
            return []

        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        view_branch = normalize_goal_scope_branch(branch)
        if not view_branch and len(normalized_keys) == 1:
            view_branch = normalize_goal_scope_branch(
                legacy_rol_branch_override(normalized_keys[0], None)
            )

        goals_by_indicator = self._goals_repository.list_resolved_goals_map(
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
            scope_branch=view_branch or None,
        )

        missing_ids = [
            item["indicator_id"]
            for item in indicators
            if item["indicator_id"] not in goals_by_indicator
        ]
        if missing_ids:
            fallback = self._goals_repository.list_latest_active_goals_map(
                indicator_ids=missing_ids,
                department_id=department_id,
                competence=period.competence,
                start_date=period.start_date,
                end_date=period.end_date,
                scope_branch=view_branch or None,
            )
            for indicator_id, goal in fallback.items():
                if indicator_id not in goals_by_indicator:
                    goals_by_indicator[indicator_id] = goal

        indicator_ids = [item["indicator_id"] for item in indicators]
        consolidated_by_indicator = self._goals_repository.list_resolved_goals_map(
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
            scope_branch=None,
        )
        branch_goals_by_indicator = self._goals_repository.list_branch_scoped_goals_map(
            indicator_ids=indicator_ids,
            department_id=department_id,
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
        )

        indicators_by_source_key = {
            str(item.get("source_key") or "").strip(): item
            for item in indicators
            if item.get("source_key")
        }
        if COMMERCIAL_ROL_SOURCE_KEY in indicators_by_source_key:
            rol_indicator = indicators_by_source_key[COMMERCIAL_ROL_SOURCE_KEY]
            for legacy_key in normalized_keys:
                if legacy_key not in indicators_by_source_key:
                    indicators_by_source_key[legacy_key] = rol_indicator

        items: list[dict] = []
        for requested_key in normalized_keys:
            indicator = indicators_by_source_key.get(requested_key)
            if not indicator:
                continue

            indicator_id = indicator["indicator_id"]
            item_view_branch = normalize_goal_scope_branch(
                legacy_rol_branch_override(requested_key, branch) or branch
            )
            goal = self._resolve_goal_for_view(
                indicator=indicator,
                indicator_id=indicator_id,
                item_view_branch=item_view_branch,
                goals_by_indicator=goals_by_indicator,
                branch_goals_by_indicator=branch_goals_by_indicator,
                period=period,
            )
            goal_scope_hint = None
            if goal is None:
                goal_scope_hint = resolve_goal_scope_hint_for_view(
                    view_branch=item_view_branch,
                    consolidated_goal=consolidated_by_indicator.get(indicator_id),
                    branch_goals=branch_goals_by_indicator.get(indicator_id),
                )

            serialized = self._serialize_item(
                indicator=indicator,
                goal=goal,
                period=period,
                view_branch=item_view_branch,
                goal_scope_hint=goal_scope_hint,
            )
            serialized["source_key"] = requested_key
            items.append(serialized)

        return items

    def _resolve_goal_for_view(
        self,
        *,
        indicator: dict,
        indicator_id: str,
        item_view_branch: str,
        goals_by_indicator: dict[str, dict],
        branch_goals_by_indicator: dict[str, dict[str, dict]],
        period,
    ) -> dict | None:
        if item_view_branch:
            branch_goal = (branch_goals_by_indicator.get(indicator_id) or {}).get(
                item_view_branch
            )
            if branch_goal:
                return {
                    **branch_goal,
                    "goal_scope_branch": item_view_branch,
                }

        resolved = goals_by_indicator.get(indicator_id)
        if resolved is not None:
            resolved_scope = normalize_goal_scope_branch(
                resolved.get("goal_scope_branch")
            )
            if not item_view_branch or resolved_scope == item_view_branch:
                return resolved
            if item_view_branch and resolved_scope != item_view_branch:
                return None

        if item_view_branch:
            return None

        return self._aggregate_branch_goals_for_consolidated_view(
            indicator=indicator,
            indicator_id=indicator_id,
            branch_goals_by_indicator=branch_goals_by_indicator,
            period=period,
        )

    def _aggregate_branch_goals_for_consolidated_view(
        self,
        *,
        indicator: dict,
        indicator_id: str,
        branch_goals_by_indicator: dict[str, dict[str, dict]],
        period,
    ) -> dict | None:
        """Rollup 01+02 via branch_value_aggregation (mesmo critério do painel SI)."""
        branch_value_aggregation = indicator.get("branch_value_aggregation")
        if is_source_consolidated_mode(branch_value_aggregation):
            return None

        by_branch = branch_goals_by_indicator.get(indicator_id) or {}
        branch_goals = [
            by_branch[code]
            for code in BRANCH_UNIT_CODES
            if by_branch.get(code) and by_branch[code].get("goal_value") is not None
        ]
        if len(branch_goals) < 2:
            return None

        value_unit = indicator.get("value_unit")
        raw_values = [float(goal["goal_value"]) for goal in branch_goals]
        aggregated_value = aggregate_branch_goal_values(
            raw_values,
            branch_value_aggregation=branch_value_aggregation,
            value_unit=value_unit,
        )
        if aggregated_value is None:
            return None

        template = branch_goals[0]
        goal_periodicity = (template.get("goal_periodicity") or "monthly").strip() or "monthly"
        goal_mode = (template.get("goal_mode") or "standard").strip() or "standard"
        # Curva mensal: agrega a meta de referência (Meta mês) por filial.
        # Nunca embutir o comparable já rateado como goal_value + mode standard —
        # o serialize recalcularia a fração MTD e aplicaria proporção em dobro.
        if goal_mode.lower() == "monthly_curve":
            reference_parts: list[float] = []
            for goal in branch_goals:
                reference = self._calculator.resolve_reference_goal(
                    goal_value=float(goal["goal_value"])
                    if goal.get("goal_value") is not None
                    else None,
                    goal_periodicity=(goal.get("goal_periodicity") or "monthly"),
                    goal_mode=(goal.get("goal_mode") or "monthly_curve"),
                    monthly_targets=goal.get("monthly_targets") or [],
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                )
                if reference is not None:
                    reference_parts.append(float(reference))
            if len(reference_parts) < 2:
                return None
            aggregated_reference = aggregate_branch_goal_values(
                reference_parts,
                branch_value_aggregation=branch_value_aggregation,
                value_unit=value_unit,
            )
            if aggregated_reference is None:
                return None
            # standard + goal_value = Meta mês consolidada → serialize aplica
            # comparable (META PARCIAL) uma única vez no período do filtro.
            return {
                "goal_label": template.get("goal_label"),
                "goal_value": aggregated_reference,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "goal_scope_branch": "",
                "monthly_targets": [],
                "aggregated_from_branches": True,
            }

        aggregation_mode = normalize_branch_value_aggregation(branch_value_aggregation)
        label = template.get("goal_label")
        if not label and aggregated_value is not None:
            label = str(aggregated_value)

        return {
            "goal_label": label,
            "goal_value": aggregated_value,
            "goal_periodicity": goal_periodicity,
            "goal_mode": goal_mode,
            "goal_scope_branch": "",
            "monthly_targets": template.get("monthly_targets") or [],
            "aggregated_from_branches": True,
            "branch_value_aggregation": aggregation_mode,
        }

    def _serialize_item(
        self,
        *,
        indicator: dict,
        goal: dict | None,
        period,
        view_branch: str,
        goal_scope_hint: str | None,
    ) -> dict:
        goal_value = float(goal["goal_value"]) if goal and goal.get("goal_value") is not None else None
        goal_mode = (goal.get("goal_mode") if goal else None) or "standard"
        goal_periodicity = (goal.get("goal_periodicity") if goal else None) or "monthly"
        monthly_targets = (goal.get("monthly_targets") if goal else None) or []
        comparable_goal = None
        reference_goal = None
        goal_flags = self._calculator.resolve_goal_period_flags(
            start_date=period.start_date,
            end_date=period.end_date,
            competence=period.competence,
            value_unit=indicator.get("value_unit"),
            indicator_id=indicator.get("indicator_id"),
        )
        if goal:
            reference_goal = self._calculator.resolve_reference_goal(
                goal_value=goal_value,
                goal_periodicity=goal_periodicity,
                goal_mode=goal_mode,
                monthly_targets=monthly_targets,
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
            )
            if goal_value is not None or (goal_mode or "").strip().lower() == "monthly_curve":
                comparable_goal = self._calculator.calculate_comparable_goal(
                    goal_value=float(goal_value or 0),
                    goal_periodicity=goal_periodicity,
                    goal_mode=goal_mode,
                    monthly_targets=monthly_targets,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    competence=period.competence,
                    value_unit=indicator.get("value_unit"),
                    indicator_id=indicator.get("indicator_id"),
                )

        goal_scope_branch = (
            normalize_goal_scope_branch(goal.get("goal_scope_branch"))
            if goal
            else ""
        )
        has_resolved_goal = goal is not None and (
            (comparable_goal is not None and comparable_goal > 0)
            or bool(goal.get("goal_label"))
        )

        return {
            "source_key": indicator.get("source_key"),
            "indicator_id": indicator.get("indicator_id"),
            "indicator_name": indicator.get("indicator_name"),
            "department_id": indicator.get("department_id"),
            "scope_type": indicator.get("scope_type"),
            "goal_scope_branch": goal_scope_branch,
            "goal_scope_label": format_goal_scope_label(goal_scope_branch)
            if has_resolved_goal
            else None,
            "goal_scope_hint": goal_scope_hint,
            "view_branch": view_branch or None,
            "performance_direction": indicator.get("performance_direction"),
            "value_unit": indicator.get("value_unit"),
            "value_prefix": indicator.get("value_prefix"),
            "value_suffix": indicator.get("value_suffix"),
            "value_decimals": int(indicator.get("value_decimals") or 2),
            "goal_label": goal.get("goal_label") if goal else None,
            "goal_value": goal_value,
            "goal_periodicity": goal.get("goal_periodicity") if goal else None,
            "goal_mode": goal.get("goal_mode") if goal else None,
            "comparable_goal": comparable_goal,
            "reference_goal": reference_goal,
            "goal_aggregation": goal_flags["goal_aggregation"],
            "goal_period_kind": goal_flags["goal_period_kind"],
            "goal_period_partial": goal_flags["goal_period_partial"],
            "has_goal": has_resolved_goal,
            "monthly_targets": goal.get("monthly_targets") if goal else [],
        }
