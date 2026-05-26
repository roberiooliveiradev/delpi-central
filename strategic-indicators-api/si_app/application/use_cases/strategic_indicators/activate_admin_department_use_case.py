from __future__ import annotations

from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)


class ActivateStrategicIndicatorsAdminDepartmentUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsAdminDepartmentsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
    ) -> dict:
        if not department_id.strip():
            raise ValueError("department_id é obrigatório.")

        return self._repository.activate_department(
            department_id=department_id.strip(),
            actor_user_id=actor_user_id,
        )