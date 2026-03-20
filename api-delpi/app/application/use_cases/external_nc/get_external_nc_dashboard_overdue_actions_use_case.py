# app/application/use_cases/external_nc/get_external_nc_dashboard_overdue_actions_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nc_dashboard_repository import (
    ExternalNcDashboardRepositoryPort,
)


class GetExternalNcDashboardOverdueActionsUseCase:
    def __init__(
        self,
        dashboard_repository: ExternalNcDashboardRepositoryPort,
    ) -> None:
        self._dashboard_repository = dashboard_repository

    def execute(self) -> list[dict]:
        return self._dashboard_repository.get_overdue_actions()