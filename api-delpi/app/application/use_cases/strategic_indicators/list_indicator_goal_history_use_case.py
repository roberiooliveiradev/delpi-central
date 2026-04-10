from __future__ import annotations

from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class ListStrategicIndicatorsIndicatorGoalHistoryUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> list[dict]:
        if not indicator_id.strip():
            raise ValueError("indicator_id é obrigatório.")

        return self._repository.list_indicator_goal_history(
            indicator_id=indicator_id.strip(),
            goal_year=goal_year,
        )