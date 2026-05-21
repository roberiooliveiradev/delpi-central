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

        goals_by_indicator = self._indicator_goals_repository.list_resolved_goals_map(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            department_id=department_id,
            scope_branch=branch,
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

        resolved: list[StrategicIndicatorCatalogItem] = []

        for item in structural_items:
            goal = goals_by_indicator.get(item.indicator_id)
            if not goal:
                logger.warning(
                    "si_goal_missing indicator_id=%s competence=%s",
                    item.indicator_id,
                    competence,
                )
                continue

            resolved.append(
                StrategicIndicatorCatalogItem(
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
                )
            )

        return resolved
