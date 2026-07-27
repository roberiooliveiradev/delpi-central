from __future__ import annotations

from app.application.dto.transformometro.dashboard_evolucao_request import (
    DashboardEvolucaoRequest,
)
from app.application.dto.transformometro.dashboard_evolucao_response import (
    DashboardEvolucaoResponse,
)
from app.domain.ports.transformometro.dashboard_port import TransformometroDashboardPort
from app.infrastructure.http.auth_header import bearer_authorization_from_context


class GetDashboardEvolucaoUseCase:
    def __init__(self, gateway: TransformometroDashboardPort) -> None:
        self._gateway = gateway

    def execute(self, request: DashboardEvolucaoRequest) -> DashboardEvolucaoResponse:
        return self._gateway.get_evolucao(
            request,
            authorization=bearer_authorization_from_context(),
        )
