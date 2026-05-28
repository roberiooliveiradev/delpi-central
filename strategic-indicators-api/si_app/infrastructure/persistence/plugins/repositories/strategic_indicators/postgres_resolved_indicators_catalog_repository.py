from __future__ import annotations

import logging

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
)
from si_app.domain.ports.strategic_indicators.resolved_indicators_catalog_repository_port import (
    StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_catalog_repository import (
    PostgresStrategicIndicatorsCatalogRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)
from si_app.shared.branch_scoped_goals import (
    format_branch_scoped_goal_label,
    pick_primary_branch_goal,
)
from si_app.shared.goal_scope import (
    is_branch_unit_scope,
    missing_goal_label_for_view,
    normalize_goal_scope_branch,
)

logger = logging.getLogger("strategic_indicators.catalog")


class PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository(
    StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
):
    def __init__(self, connection=None):
        self._catalog_repository = PostgresStrategicIndicatorsCatalogRepository(connection)
        self._indicator_goals_repository = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection)

    def list_resolved_indicators_catalog(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> list[StrategicIndicatorCatalogItem]:
        structural_items = self._catalog_repository.list_structural_indicators_catalog(
            department_id=department_id,
        )
        departments_catalog = self._catalog_repository.list_departments_catalog()
        aggregation_by_department = {
            item.department_id: (item.aggregation_mode or "consolidated").strip()
            for item in departments_catalog
        }

        view_branch = normalize_goal_scope_branch(branch)
        goals_by_indicator = self._resolve_goals_for_view(
            structural_items=structural_items,
            aggregation_by_department=aggregation_by_department,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            view_branch=view_branch,
        )

        missing_indicator_ids = [
            item.indicator_id
            for item in structural_items
            if item.indicator_id not in goals_by_indicator
        ]
        if missing_indicator_ids:
            fallback_goals = self._indicator_goals_repository.list_latest_active_goals_map(
                indicator_ids=missing_indicator_ids,
                department_id=department_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                scope_branch=branch,
            )
            for indicator_id, goal in fallback_goals.items():
                if indicator_id not in goals_by_indicator:
                    goals_by_indicator[indicator_id] = goal
                    logger.info(
                        "si_goal_year_fallback indicator_id=%s competence=%s goal_year=%s",
                        indicator_id,
                        competence,
                        goal.get("goal_year"),
                    )

        per_unit_indicator_ids = [
            item.indicator_id
            for item in structural_items
            if (item.scope_type or "").strip() == "per_unit"
        ]

        # Sempre carrega branch_goals para indicadores per_unit. Na visão por filial
        # eles podem ser a ÚNICA fonte de meta (e sem isso a UI cai em 0,00).
        branch_goals_by_indicator: dict[str, dict[str, dict]] = {}
        if per_unit_indicator_ids:
            branch_goals_by_indicator = (
                self._indicator_goals_repository.list_branch_scoped_goals_map(
                    indicator_ids=per_unit_indicator_ids,
                    department_id=department_id,
                    competence=competence,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        if not normalize_goal_scope_branch(branch):

            still_missing = [
                item.indicator_id
                for item in structural_items
                if (
                    item.indicator_id not in goals_by_indicator
                    and item.indicator_id not in branch_goals_by_indicator
                )
            ]
            if still_missing:
                extra_branch_goals = (
                    self._indicator_goals_repository.list_branch_scoped_goals_map(
                        indicator_ids=still_missing,
                        department_id=department_id,
                        competence=competence,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                for indicator_id, branch_map in extra_branch_goals.items():
                    if branch_map:
                        branch_goals_by_indicator[indicator_id] = branch_map

        if not normalize_goal_scope_branch(branch):
            still_missing_for_branch = [
                item.indicator_id
                for item in structural_items
                if (
                    item.indicator_id not in goals_by_indicator
                    and item.indicator_id not in branch_goals_by_indicator
                )
            ]
            if still_missing_for_branch:
                expired_branch_goals = (
                    self._indicator_goals_repository.list_branch_scoped_goals_ignoring_validity(
                        indicator_ids=still_missing_for_branch,
                        department_id=department_id,
                        competence=competence,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                for indicator_id, bg in expired_branch_goals.items():
                    if indicator_id not in branch_goals_by_indicator:
                        branch_goals_by_indicator[indicator_id] = bg
                        logger.info(
                            "si_branch_goal_validity_fallback indicator_id=%s competence=%s branches=%s",
                            indicator_id,
                            competence,
                            list(bg.keys()),
                        )

        final_missing_ids = [
            item.indicator_id
            for item in structural_items
            if (
                item.indicator_id not in goals_by_indicator
                and item.indicator_id not in branch_goals_by_indicator
            )
        ]
        expired_goals_by_indicator: dict[str, dict] = {}
        if final_missing_ids:
            expired_goals_by_indicator = (
                self._indicator_goals_repository.list_latest_goals_ignoring_validity(
                    indicator_ids=final_missing_ids,
                    department_id=department_id,
                    competence=competence,
                    scope_branch=branch,
                )
            )
            for indicator_id, goal in expired_goals_by_indicator.items():
                logger.info(
                    "si_goal_validity_fallback indicator_id=%s competence=%s goal_year=%s valid_to=%s",
                    indicator_id,
                    competence,
                    goal.get("goal_year"),
                    goal.get("valid_to"),
                )

        resolved: list[StrategicIndicatorCatalogItem] = []

        for item in structural_items:
            goal = goals_by_indicator.get(item.indicator_id)
            branch_goals = branch_goals_by_indicator.get(item.indicator_id, {})
            scope_type = (item.scope_type or "").strip()

            if (
                is_branch_unit_scope(view_branch)
                and scope_type == "per_unit"
                and branch_goals
                and view_branch in branch_goals
            ):
                view_goal = dict(branch_goals[view_branch] or {})
                view_goal["goal_scope_branch"] = view_branch
                resolved.append(
                    self._catalog_item_from_goal(
                        item,
                        view_goal,
                        branch_goals={view_branch: branch_goals[view_branch]},
                    )
                )
                continue

            if branch_goals and scope_type == "per_unit":
                resolved.append(self._catalog_item_from_branch_goals(item, branch_goals))
                continue

            if goal:
                resolved.append(
                    self._catalog_item_from_goal(
                        item,
                        goal,
                        branch_goals=branch_goals,
                    )
                )
                continue

            if branch_goals:
                resolved.append(self._catalog_item_from_branch_goals(item, branch_goals))
                continue

            expired_goal = expired_goals_by_indicator.get(item.indicator_id)
            if expired_goal:
                resolved.append(
                    self._catalog_item_from_goal(item, expired_goal, branch_goals={})
                )
                continue

            if is_branch_unit_scope(view_branch):
                resolved.append(
                    self._catalog_item_missing_goal_for_branch_view(
                        item,
                        view_branch=view_branch,
                    )
                )
                continue

            logger.warning(
                "si_goal_missing indicator_id=%s competence=%s",
                item.indicator_id,
                competence,
            )
            resolved.append(self._catalog_item_without_goal(item))

        return resolved

    def _resolve_goals_for_view(
        self,
        *,
        structural_items: list[StrategicIndicatorCatalogItem],
        aggregation_by_department: dict[str, str],
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        department_id: str | None,
        view_branch: str,
    ) -> dict[str, dict]:
        """
        Visão filial: departamentos `average_of_units` usam meta 01/02;
        departamentos `consolidated` repetem meta consolidada (mesmo IDD da visão consolidado).
        """
        if not is_branch_unit_scope(view_branch):
            return self._indicator_goals_repository.list_resolved_goals_map(
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                department_id=department_id,
                scope_branch=view_branch,
            )

        consolidated_dept_ids = {
            dept_id
            for dept_id, mode in aggregation_by_department.items()
            if mode != "average_of_units"
        }

        goals_consolidated = self._indicator_goals_repository.list_resolved_goals_map(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            scope_branch="",
        )
        goals_branch = self._indicator_goals_repository.list_resolved_goals_map(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            scope_branch=view_branch,
        )

        merged: dict[str, dict] = {}
        for item in structural_items:
            if item.department_id in consolidated_dept_ids:
                goal = goals_consolidated.get(item.indicator_id)
            else:
                goal = goals_branch.get(item.indicator_id)
            if goal is not None:
                merged[item.indicator_id] = goal

        return merged

    @staticmethod
    def _catalog_item_from_goal(
        item: StrategicIndicatorCatalogItem,
        goal: dict,
        *,
        branch_goals: dict[str, dict],
    ) -> StrategicIndicatorCatalogItem:
        return StrategicIndicatorCatalogItem(
            indicator_id=item.indicator_id,
            department_id=item.department_id,
            indicator_name=item.indicator_name,
            weight_pct=item.weight_pct,
            goal_label=goal["goal_label"],
            goal_value=float(goal["goal_value"]),
            goal_periodicity=goal["goal_periodicity"],
            goal_mode=goal.get("goal_mode", "standard"),
            monthly_targets=goal.get("monthly_targets") or [],
            scope_type=item.scope_type,
            performance_direction=getattr(
                item,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=item.strategic_description,
            source_key=item.source_key,
            value_unit=item.value_unit,
            value_prefix=item.value_prefix,
            value_suffix=item.value_suffix,
            value_decimals=item.value_decimals,
            branch_goals=branch_goals,
            resolved_goal_scope_branch=normalize_goal_scope_branch(
                goal.get("goal_scope_branch"),
            ),
            has_resolved_goal=True,
        )

    @staticmethod
    def _catalog_item_without_goal(
        item: StrategicIndicatorCatalogItem,
    ) -> StrategicIndicatorCatalogItem:
        return StrategicIndicatorCatalogItem(
            indicator_id=item.indicator_id,
            department_id=item.department_id,
            indicator_name=item.indicator_name,
            weight_pct=item.weight_pct,
            goal_label=item.goal_label or "Meta não definida",
            goal_value=item.goal_value or 0.0,
            goal_periodicity=item.goal_periodicity or "monthly",
            goal_mode="standard",
            monthly_targets=[],
            scope_type=item.scope_type,
            performance_direction=getattr(
                item,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=item.strategic_description,
            source_key=item.source_key,
            value_unit=item.value_unit,
            value_prefix=item.value_prefix,
            value_suffix=item.value_suffix,
            value_decimals=item.value_decimals,
            branch_goals={},
            resolved_goal_scope_branch="",
            has_resolved_goal=False,
        )

    @staticmethod
    def _catalog_item_missing_goal_for_branch_view(
        item: StrategicIndicatorCatalogItem,
        *,
        view_branch: str,
    ) -> StrategicIndicatorCatalogItem:
        return StrategicIndicatorCatalogItem(
            indicator_id=item.indicator_id,
            department_id=item.department_id,
            indicator_name=item.indicator_name,
            weight_pct=item.weight_pct,
            goal_label=missing_goal_label_for_view(view_branch),
            goal_value=0.0,
            goal_periodicity="monthly",
            goal_mode="standard",
            monthly_targets=[],
            scope_type=item.scope_type,
            performance_direction=getattr(
                item,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=item.strategic_description,
            source_key=item.source_key,
            value_unit=item.value_unit,
            value_prefix=item.value_prefix,
            value_suffix=item.value_suffix,
            value_decimals=item.value_decimals,
            branch_goals={},
            resolved_goal_scope_branch="",
            has_resolved_goal=False,
        )

    @staticmethod
    def _catalog_item_from_branch_goals(
        item: StrategicIndicatorCatalogItem,
        branch_goals: dict[str, dict],
    ) -> StrategicIndicatorCatalogItem:
        primary_goal = pick_primary_branch_goal(branch_goals)
        return StrategicIndicatorCatalogItem(
            indicator_id=item.indicator_id,
            department_id=item.department_id,
            indicator_name=item.indicator_name,
            weight_pct=item.weight_pct,
            goal_label=format_branch_scoped_goal_label(branch_goals),
            goal_value=float(primary_goal["goal_value"]),
            goal_periodicity=primary_goal["goal_periodicity"],
            goal_mode=primary_goal.get("goal_mode", "standard"),
            monthly_targets=primary_goal.get("monthly_targets") or [],
            scope_type=item.scope_type,
            performance_direction=getattr(
                item,
                "performance_direction",
                "higher_is_better",
            ),
            strategic_description=item.strategic_description,
            source_key=item.source_key,
            value_unit=item.value_unit,
            value_prefix=item.value_prefix,
            value_suffix=item.value_suffix,
            value_decimals=item.value_decimals,
            branch_goals=branch_goals,
            resolved_goal_scope_branch="",
            has_resolved_goal=True,
        )
