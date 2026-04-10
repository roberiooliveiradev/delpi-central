from __future__ import annotations

from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class ListStrategicIndicatorsIndicatorGoalsUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        indicator_id: str | None = None,
        goal_year: int | None = None,
        department_id: str | None = None,
        active_only: bool = False,
    ) -> list[dict]:
        return self._repository.list_indicator_goals(
            indicator_id=indicator_id,
            goal_year=goal_year,
            department_id=department_id,
            active_only=active_only,
        )