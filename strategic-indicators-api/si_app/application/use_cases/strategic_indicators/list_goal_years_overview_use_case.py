from __future__ import annotations

from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class ListStrategicIndicatorsGoalYearsOverviewUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self) -> list[dict]:
        return self._repository.list_goal_years_overview()