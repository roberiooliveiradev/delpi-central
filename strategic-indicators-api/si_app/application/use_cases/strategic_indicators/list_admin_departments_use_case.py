from __future__ import annotations

from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)


class ListStrategicIndicatorsAdminDepartmentsUseCase:
    def __init__(
        self,
        repository: StrategicIndicatorsAdminDepartmentsRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self) -> list[dict]:
        return self._repository.list_departments()