from __future__ import annotations

from app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
)
from app.domain.ports.strategic_indicators.resolved_indicators_catalog_repository_port import (
    StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_catalog_repository import (
    PostgresStrategicIndicatorsCatalogRepository,
)
from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)


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
    ) -> list[StrategicIndicatorCatalogItem]:
        structural_items = self._catalog_repository.list_structural_indicators_catalog(
            department_id=department_id,
        )

        resolved: list[StrategicIndicatorCatalogItem] = []

        for item in structural_items:
            goal = self._indicator_goals_repository.get_resolved_goal(
                indicator_id=item.indicator_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
            )
            if not goal:
                raise ValueError(
                    f"Meta não encontrada para indicator_id={item.indicator_id}"
                )

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
                    performance_direction=getattr(item, "performance_direction", "higher_is_better"),
                    strategic_description=item.strategic_description,
                    source_key=item.source_key,
                )
            )

        return resolved