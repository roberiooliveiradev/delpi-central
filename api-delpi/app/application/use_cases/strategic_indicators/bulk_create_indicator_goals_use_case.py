from __future__ import annotations

from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class BulkCreateStrategicIndicatorsIndicatorGoalsUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}

    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        body: dict,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        goal_year = int(body.get("goal_year") or 0)
        items = body.get("items") or []

        if goal_year < 2020 or goal_year > 2100:
            raise ValueError("goal_year inválido.")

        if not isinstance(items, list) or not items:
            raise ValueError("items deve ser uma lista não vazia.")

        for item in items:
            if not (item.get("indicator_id") or "").strip():
                raise ValueError("indicator_id é obrigatório em todas as metas.")
            if not (item.get("goal_label") or "").strip():
                raise ValueError("goal_label é obrigatório em todas as metas.")
            if float(item.get("goal_value") or 0) < 0:
                raise ValueError("goal_value não pode ser negativo.")
            if (item.get("goal_periodicity") or "").strip() not in self.VALID_PERIODICITIES:
                raise ValueError("goal_periodicity inválido.")

        return self._repository.bulk_create_indicator_goals(
            goal_year=goal_year,
            items=items,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )