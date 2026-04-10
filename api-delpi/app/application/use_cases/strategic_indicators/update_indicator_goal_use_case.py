from __future__ import annotations

from app.application.dto.strategic_indicators.update_indicator_goal_request import (
    UpdateStrategicIndicatorsIndicatorGoalRequest,
)
from app.application.use_cases.strategic_indicators.create_indicator_goal_use_case import (
    StrategicIndicatorsIndicatorGoalValidationError,
)
from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class UpdateStrategicIndicatorsIndicatorGoalUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}

    def __init__(
        self,
        repository: StrategicIndicatorsIndicatorGoalsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        request: UpdateStrategicIndicatorsIndicatorGoalRequest,
    ) -> dict:
        self._validate_request(request)

        return self._repository.update_indicator_goal(
            goal_id=request.goal_id,
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
        request: UpdateStrategicIndicatorsIndicatorGoalRequest,
    ) -> None:
        if not request.goal_id.strip():
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_id é obrigatório."
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