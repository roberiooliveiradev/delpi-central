from __future__ import annotations

from si_app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class FillMissingStrategicIndicatorsIndicatorGoalsUseCase:
    def __init__(
        self,
        goals_repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
        indicators_repository: StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
    ) -> None:
        self._goals_repository = goals_repository
        self._indicators_repository = indicators_repository

    def execute(
        self,
        *,
        body: dict,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        goal_year = int(body.get("goal_year") or 0)
        department_ids = body.get("department_ids") or []
        copy_from_year = body.get("copy_from_year")

        if goal_year < 2020 or goal_year > 2100:
            raise ValueError("goal_year inválido.")

        if copy_from_year is not None:
            copy_from_year = int(copy_from_year)
            if copy_from_year < 2020 or copy_from_year > 2100:
                raise ValueError("copy_from_year inválido.")

        indicator_ids = self._indicators_repository.list_indicator_ids_by_departments(
            department_ids=department_ids if department_ids else None,
        )

        return self._goals_repository.fill_missing_goals(
            goal_year=goal_year,
            indicator_ids=indicator_ids,
            copy_from_year=copy_from_year,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )