from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
        PluginBaseRepository,
    )


def delete_indicator_goals_cascade(
    repository: PluginBaseRepository,
    *,
    indicator_id: str,
) -> None:
    repository.execute(
        """
        DELETE FROM strategic_indicators.indicator_goal_monthly_targets
        WHERE indicator_goal_id IN (
            SELECT id
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
        )
        """,
        (indicator_id,),
    )
    repository.execute(
        """
        UPDATE strategic_indicators.indicator_goals
        SET copied_from_goal_id = NULL
        WHERE copied_from_goal_id IN (
            SELECT id
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
        )
        """,
        (indicator_id,),
    )
    repository.execute(
        """
        DELETE FROM strategic_indicators.indicator_goals
        WHERE indicator_id = %s
        """,
        (indicator_id,),
    )


def delete_indicator_goal_hard(
    repository: PluginBaseRepository,
    *,
    goal_id: str,
) -> None:
    repository.execute(
        """
        DELETE FROM strategic_indicators.indicator_goal_monthly_targets
        WHERE indicator_goal_id = %s
        """,
        (goal_id,),
    )
    repository.execute(
        """
        UPDATE strategic_indicators.indicator_goals
        SET copied_from_goal_id = NULL
        WHERE copied_from_goal_id = %s
        """,
        (goal_id,),
    )
    repository.execute(
        """
        DELETE FROM strategic_indicators.indicator_goals
        WHERE id = %s
        """,
        (goal_id,),
    )
