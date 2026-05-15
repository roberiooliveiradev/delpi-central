from __future__ import annotations

from si_app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)


class ListStrategicIndicatorsAdminDepartmentIndicatorsUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        department_id: str,
    ) -> list[dict]:
        if not department_id.strip():
            raise ValueError("department_id é obrigatório.")

        return self._repository.list_department_indicators(
            department_id=department_id.strip(),
        )