from __future__ import annotations

from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class DeactivateStrategicIndicatorsIndicatorGoalUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        if not goal_id.strip():
            raise ValueError("goal_id é obrigatório.")

        return self._repository.deactivate_indicator_goal(
            goal_id=goal_id.strip(),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )