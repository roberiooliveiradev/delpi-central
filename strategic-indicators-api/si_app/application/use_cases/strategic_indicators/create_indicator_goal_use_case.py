from __future__ import annotations

from si_app.application.dto.strategic_indicators.create_indicator_goal_request import (
    CreateStrategicIndicatorsIndicatorGoalRequest,
)
from si_app.application.services.strategic_indicators.goal_scope_validation import (
    validate_goal_scope_branch,
)
from si_app.application.services.strategic_indicators.goal_value_policy import (
    resolve_persisted_goal_value,
)
from si_app.application.services.strategic_indicators.indicator_goal_validation_error import (
    StrategicIndicatorsIndicatorGoalValidationError,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class CreateStrategicIndicatorsIndicatorGoalUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}
    VALID_GOAL_MODES = {"standard", "monthly_curve"}

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

        monthly_targets = request.monthly_targets if request.goal_mode.strip() == "monthly_curve" else []

        policy = self._repository.get_indicator_goal_policy(request.indicator_id.strip())
        if not policy:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "indicator_id não encontrado no catálogo."
            )

        goal_scope_branch = validate_goal_scope_branch(
            goal_scope_branch=request.goal_scope_branch,
            scope_type=str(policy.get("scope_type") or "consolidated"),
        )

        return self._repository.create_indicator_goal(
            indicator_id=request.indicator_id.strip(),
            goal_year=request.goal_year,
            goal_label=request.goal_label.strip(),
            goal_value=resolve_persisted_goal_value(
                goal_mode=request.goal_mode.strip(),
                goal_value=float(request.goal_value),
            ),
            goal_periodicity=request.goal_periodicity.strip(),
            goal_mode=request.goal_mode.strip(),
            goal_scope_branch=goal_scope_branch,
            monthly_targets=monthly_targets,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            notes=request.notes.strip() if request.notes else None,
            actor_user_id=request.actor_user_id,
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

        goal_mode = request.goal_mode.strip()

        if goal_mode != "monthly_curve" and float(request.goal_value) < 0:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_value não pode ser negativo."
            )

        periodicity = request.goal_periodicity.strip()
        if periodicity not in self.VALID_PERIODICITIES:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_periodicity inválido."
            )

        if goal_mode not in self.VALID_GOAL_MODES:
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_mode inválido."
            )

        if goal_mode == "monthly_curve":
            if len(request.monthly_targets) != 12:
                raise StrategicIndicatorsIndicatorGoalValidationError(
                    "monthly_targets deve conter exatamente 12 meses."
                )

            months = sorted(
                int(item.get("month_number") or 0)
                for item in request.monthly_targets
            )
            if months != list(range(1, 13)):
                raise StrategicIndicatorsIndicatorGoalValidationError(
                    "monthly_targets deve conter os meses de 1 a 12 sem repetição."
                )

            for item in request.monthly_targets:
                if float(item.get("target_value") or 0) < 0:
                    raise StrategicIndicatorsIndicatorGoalValidationError(
                        "target_value não pode ser negativo."
                    )
        else:
            if request.monthly_targets:
                raise StrategicIndicatorsIndicatorGoalValidationError(
                    "monthly_targets só pode ser informado quando goal_mode=monthly_curve."
                )