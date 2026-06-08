from __future__ import annotations

import logging

from si_app.application.use_cases.strategic_indicators.period_resolution import (
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
                indicator_id=indicator_id,
                item_view_branch=item_view_branch,
                goals_by_indicator=goals_by_indicator,
                branch_goals_by_indicator=branch_goals_by_indicator,
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

    @staticmethod
    def _resolve_goal_for_view(
        *,
        indicator_id: str,
        item_view_branch: str,
        goals_by_indicator: dict[str, dict],
        branch_goals_by_indicator: dict[str, dict[str, dict]],
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
        if resolved is None:
            return None

        resolved_scope = normalize_goal_scope_branch(
            resolved.get("goal_scope_branch")
        )
        if item_view_branch and resolved_scope != item_view_branch:
            return None

        return resolved

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
        comparable_goal = None
        if goal and goal_value is not None:
            comparable_goal = self._calculator.calculate_comparable_goal(
                goal_value=goal_value,
                goal_periodicity=goal.get("goal_periodicity") or "monthly",
                goal_mode=goal.get("goal_mode") or "standard",
                monthly_targets=goal.get("monthly_targets") or [],
                start_date=period.start_date,
                end_date=period.end_date,
                competence=period.competence,
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
            "has_goal": has_resolved_goal,
            "monthly_targets": goal.get("monthly_targets") if goal else [],
        }
