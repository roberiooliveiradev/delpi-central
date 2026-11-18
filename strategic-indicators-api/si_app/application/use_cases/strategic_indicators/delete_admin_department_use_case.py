from __future__ import annotations

from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
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
        expected_xmin: str | None = None,
        expected_indicator_count: int | None = None,
        expected_goal_count: int | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        if not department_id.strip():
            raise ValueError("department_id é obrigatório.")

        return self._repository.delete_department(
            department_id=department_id.strip(),
            actor_user_id=actor_user_id,
            expected_xmin=expected_xmin,
            expected_indicator_count=expected_indicator_count,
            expected_goal_count=expected_goal_count,
            audit_origin=audit_origin,
            correlation_id=correlation_id,
        )
