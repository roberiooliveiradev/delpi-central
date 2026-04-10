from __future__ import annotations

from app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)


class DeleteStrategicIndicatorsAdminDepartmentUseCase:
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
        actor_email: str | None,
    ) -> dict:
        if not department_id.strip():
            raise ValueError("department_id é obrigatório.")

        return self._repository.delete_department(
            department_id=department_id.strip(),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )