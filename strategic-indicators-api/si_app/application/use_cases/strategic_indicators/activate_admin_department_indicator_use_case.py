from __future__ import annotations

from si_app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)


class ActivateStrategicIndicatorsAdminDepartmentIndicatorUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        if not indicator_id.strip():
            raise ValueError("indicator_id é obrigatório.")

        return self._repository.activate_department_indicator(
            indicator_id=indicator_id.strip(),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )