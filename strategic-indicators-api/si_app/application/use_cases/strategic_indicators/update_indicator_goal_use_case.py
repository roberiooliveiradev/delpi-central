from __future__ import annotations

from si_app.application.dto.strategic_indicators.update_indicator_goal_request import (
    UpdateStrategicIndicatorsIndicatorGoalRequest,
)
from si_app.application.services.strategic_indicators.goal_scope_validation import (
    validate_goal_scope_branch,
)
from si_app.application.services.strategic_indicators.indicator_goal_validation_error import (
    StrategicIndicatorsIndicatorGoalValidationError,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)


class UpdateStrategicIndicatorsIndicatorGoalUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}
    VALID_GOAL_MODES = {"standard", "monthly_curve"}

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

        monthly_targets = request.monthly_targets if request.goal_mode.strip() == "monthly_curve" else []

        indicator_id = (request.indicator_id or "").strip() or None
        goal_year = request.goal_year
        goal_scope_branch = request.goal_scope_branch

        if goal_year is not None and (goal_year < 2020 or goal_year > 2100):
            raise StrategicIndicatorsIndicatorGoalValidationError(
                "goal_year inválido."
            )

        resolved_indicator_id: str | None = None
        resolved_goal_year: int | None = None
        resolved_scope_branch: str | None = None

        if indicator_id or goal_year is not None or goal_scope_branch is not None:
            existing = self._repository.fetch_goal_identity(request.goal_id.strip())
            if not existing:
                raise StrategicIndicatorsIndicatorGoalValidationError(
                    "Meta não encontrada."
                )

            resolved_indicator_id = indicator_id or str(existing.get("indicator_id") or "")
            resolved_goal_year = (
                goal_year
                if goal_year is not None
                else int(existing.get("goal_year") or 0)
            )
            scope_input = (
                goal_scope_branch
                if goal_scope_branch is not None
                else existing.get("goal_scope_branch")
            )

            policy = self._repository.get_indicator_goal_policy(resolved_indicator_id)
            if not policy:
                raise StrategicIndicatorsIndicatorGoalValidationError(
                    "indicator_id não encontrado no catálogo."
                )

            resolved_scope_branch = validate_goal_scope_branch(
                goal_scope_branch=scope_input,
                scope_type=str(policy.get("scope_type") or "consolidated"),
            )

        return self._repository.update_indicator_goal(
            goal_id=request.goal_id,
            indicator_id=resolved_indicator_id,
            goal_year=resolved_goal_year,
            goal_scope_branch=resolved_scope_branch,
            goal_label=request.goal_label.strip(),
            goal_value=float(request.goal_value),
            goal_periodicity=request.goal_periodicity.strip(),
            goal_mode=request.goal_mode.strip(),
            monthly_targets=monthly_targets,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            notes=request.notes.strip() if request.notes else None,
            actor_user_id=request.actor_user_id,
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

        goal_mode = request.goal_mode.strip()
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