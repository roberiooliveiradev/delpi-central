from __future__ import annotations

from app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)
from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class DuplicateStrategicIndicatorsIndicatorGoalsYearUseCase:
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
        source_year = int(body.get("source_year") or 0)
        target_year = int(body.get("target_year") or 0)
        department_ids = body.get("department_ids") or []
        overwrite_existing = bool(body.get("overwrite_existing", False))

        if source_year < 2020 or source_year > 2100:
            raise ValueError("source_year inválido.")
        if target_year < 2020 or target_year > 2100:
            raise ValueError("target_year inválido.")
        if source_year == target_year:
            raise ValueError("source_year e target_year devem ser diferentes.")

        indicator_ids = self._indicators_repository.list_indicator_ids_by_departments(
            department_ids=department_ids if department_ids else None,
        )

        return self._goals_repository.duplicate_goals_year(
            source_year=source_year,
            target_year=target_year,
            indicator_ids=indicator_ids,
            overwrite_existing=overwrite_existing,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )