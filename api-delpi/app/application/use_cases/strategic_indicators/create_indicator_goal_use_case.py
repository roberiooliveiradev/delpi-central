from __future__ import annotations

from app.application.dto.strategic_indicators.create_indicator_goal_request import (
    CreateStrategicIndicatorsIndicatorGoalRequest,
)
from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class StrategicIndicatorsIndicatorGoalValidationError(ValueError):
    """Erro de validação das metas analíticas do Strategic Indicators."""


class CreateStrategicIndicatorsIndicatorGoalUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}

    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        request: CreateStrategicIndicatorsIndicatorGoalRequest,
    ) -> dict:
        self._validate_request(request)

        return self._repository.create_indicator_goal(
            indicator_id=request.indicator_id.strip(),
            goal_year=request.goal_year,
            goal_label=request.goal_label.strip(),
            goal_value=float(request.goal_value),
            goal_periodicity=request.goal_periodicity.strip(),
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            notes=request.notes.strip() if request.notes else None,
            actor_user_id=request.actor_user_id,
            actor_email=request.actor_email,
        )

    def _validate_request(
        self,
        request: CreateStrategicIndicatorsIndicatorGoalRequest,
    ) -> None:
        if not request.indicator_id.strip():
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "indicator_id é obrigatório."
            )

        if request.goal_year < 2020 or request.goal_year > 2100:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_year inválido."
            )

        if not request.goal_label.strip():
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_label é obrigatório."
            )

        if float(request.goal_value) < 0:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_value não pode ser negativo."
            )

        periodicity = request.goal_periodicity.strip()
        if periodicity not in self.VALID_PERIODICITIES:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_periodicity inválido."
            )