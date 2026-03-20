# app/application/use_cases/external_nc/get_external_nc_dashboard_summary_use_case.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nc_dashboard_repository import (
    ExternalNcDashboardRepositoryPort,
)


class GetExternalNcDashboardSummaryUseCase:
    def __init__(
        self,
        dashboard_repository: ExternalNcDashboardRepositoryPort,
    ) -> None:
        self._dashboard_repository = dashboard_repository

    def execute(self) -> dict:
        return self._dashboard_repository.get_summary()