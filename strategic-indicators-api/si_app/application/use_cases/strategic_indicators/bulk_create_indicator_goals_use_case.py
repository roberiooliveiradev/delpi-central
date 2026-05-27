from __future__ import annotations

from si_app.application.services.strategic_indicators.goal_scope_validation import (
    validate_goal_scope_branch,
)
from si_app.application.services.strategic_indicators.goal_curve_validation import (
    validate_curve_targets,
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


class BulkCreateStrategicIndicatorsIndicatorGoalsUseCase:
    VALID_PERIODICITIES = {"monthly", "annual", "quarterly", "weekly"}
    VALID_GOAL_MODES = {"standard", "monthly_curve"}

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
    ) -> dict:
        goal_year = int(body.get("goal_year") or 0)
        items = body.get("items") or []

        if goal_year < 2020 or goal_year > 2100:
            raise ValueError("goal_year inválido.")

        if not isinstance(items, list) or not items:
            raise ValueError("items deve ser uma lista não vazia.")

        normalized_items: list[dict] = []

        for item in items:
            indicator_id = (item.get("indicator_id") or "").strip()
            goal_label = (item.get("goal_label") or "").strip()
            goal_periodicity = (item.get("goal_periodicity") or "").strip()
            goal_mode = (item.get("goal_mode") or "standard").strip()
            monthly_targets = item.get("monthly_targets") or []

            if not indicator_id:
                raise ValueError("indicator_id é obrigatório em todas as metas.")

            if not goal_label:
                raise ValueError("goal_label é obrigatório em todas as metas.")

            goal_value = float(item.get("goal_value") or 0)
            if goal_mode != "monthly_curve" and goal_value < 0:
                raise ValueError("goal_value não pode ser negativo.")
            goal_value = resolve_persisted_goal_value(
                goal_mode=goal_mode,
                goal_value=goal_value,
            )

            if goal_periodicity not in self.VALID_PERIODICITIES:
                raise ValueError("goal_periodicity inválido.")

            if goal_mode not in self.VALID_GOAL_MODES:
                raise ValueError("goal_mode inválido.")

            if goal_mode == "monthly_curve":
                validate_curve_targets(monthly_targets, goal_periodicity)
            else:
                if monthly_targets:
                    raise ValueError(
                        "monthly_targets só pode ser informado quando goal_mode=monthly_curve."
                    )

            policy = self._repository.get_indicator_goal_policy(indicator_id)
            if not policy:
                raise ValueError("indicator_id não encontrado no catálogo.")

            try:
                goal_scope_branch = validate_goal_scope_branch(
                    goal_scope_branch=item.get("goal_scope_branch"),
                    scope_type=str(policy.get("scope_type") or "consolidated"),
                )
            except StrategicIndicatorsIndicatorGoalValidationError as exc:
                raise ValueError(str(exc)) from exc

            normalized_items.append(
                {
                    "indicator_id": indicator_id,
                    "goal_label": goal_label,
                    "goal_value": goal_value,
                    "goal_periodicity": goal_periodicity,
                    "goal_mode": goal_mode,
                    "goal_scope_branch": goal_scope_branch,
                    "monthly_targets": monthly_targets if goal_mode == "monthly_curve" else [],
                    "valid_from": item.get("valid_from"),
                    "valid_to": item.get("valid_to"),
                    "notes": (item.get("notes") or "").strip() or None,
                }
            )

        return self._repository.bulk_create_indicator_goals(
            goal_year=goal_year,
            items=normalized_items,
            actor_user_id=actor_user_id,
        )