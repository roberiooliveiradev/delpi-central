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
from si_app.shared.goal_scope import BRANCH_UNIT_CODES, normalize_goal_scope_branch

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

        if self._goals_repository is None:
            from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
                PostgresStrategicIndicatorsIndicatorGoalsRepository,
            )

            self._goals_repository = PostgresStrategicIndicatorsIndicatorGoalsRepository()

        indicators = self._indicators_repository.list_active_indicators_by_source_keys(
            normalized_keys,
            department_id=department_id,
        )
        if not indicators:
            return []

        period = resolve_period(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        scope_branch = normalize_goal_scope_branch(branch)

        goals_by_indicator = self._goals_repository.list_resolved_goals_map(
            competence=period.competence,
            start_date=period.start_date,
            end_date=period.end_date,
            department_id=department_id,
            scope_branch=scope_branch or None,
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
                scope_branch=scope_branch or None,
            )
            for indicator_id, goal in fallback.items():
                if indicator_id not in goals_by_indicator:
                    goals_by_indicator[indicator_id] = goal

        if not scope_branch:
            still_missing = [
                item["indicator_id"]
                for item in indicators
                if item["indicator_id"] not in goals_by_indicator
            ]
            if still_missing:
                branch_goals = self._goals_repository.list_branch_scoped_goals_map(
                    indicator_ids=still_missing,
                    department_id=department_id,
                    competence=period.competence,
                    start_date=period.start_date,
                    end_date=period.end_date,
                )
                for indicator_id, by_branch in branch_goals.items():
                    merged = self._merge_branch_goals_for_consolidated_view(by_branch)
                    if merged:
                        goals_by_indicator[indicator_id] = merged

        items: list[dict] = []
        for indicator in indicators:
            goal = goals_by_indicator.get(indicator["indicator_id"])
            items.append(
                self._serialize_item(
                    indicator=indicator,
                    goal=goal,
                    period=period,
                )
            )

        return items

    def _serialize_item(
        self,
        *,
        indicator: dict,
        goal: dict | None,
        period,
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

        return {
            "source_key": indicator.get("source_key"),
            "indicator_id": indicator.get("indicator_id"),
            "indicator_name": indicator.get("indicator_name"),
            "department_id": indicator.get("department_id"),
            "scope_type": indicator.get("scope_type"),
            "goal_scope_branch": goal_scope_branch,
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
            "has_goal": comparable_goal is not None and comparable_goal > 0,
            "monthly_targets": goal.get("monthly_targets") if goal else [],
        }

    @staticmethod
    def _merge_branch_goals_for_consolidated_view(
        by_branch: dict[str, dict],
    ) -> dict | None:
        ordered_branches = [
            code
            for code in BRANCH_UNIT_CODES
            if code in by_branch and by_branch[code].get("goal_label")
        ]
        if not ordered_branches:
            ordered_branches = [
                code
                for code in sorted(by_branch.keys())
                if by_branch[code].get("goal_label")
            ]
        if not ordered_branches:
            return None

        labels = [str(by_branch[code]["goal_label"]).strip() for code in ordered_branches]
        unique_labels = list(dict.fromkeys(labels))
        base = by_branch[ordered_branches[0]]

        if len(unique_labels) == 1:
            merged_label = unique_labels[0]
        else:
            merged_label = " · ".join(
                f"{code}: {by_branch[code]['goal_label']}"
                for code in ordered_branches
                if by_branch[code].get("goal_label")
            )

        return {
            **base,
            "goal_label": merged_label,
            "goal_scope_branch": "",
        }

