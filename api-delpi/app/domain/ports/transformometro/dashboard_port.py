from __future__ import annotations

from typing import Protocol

from app.application.dto.transformometro.dashboard_evolucao_request import (
    DashboardEvolucaoRequest,
)
from app.application.dto.transformometro.dashboard_evolucao_response import (
    DashboardEvolucaoResponse,
)


class TransformometroDashboardPort(Protocol):
    def get_evolucao(
        self,
        request: DashboardEvolucaoRequest,
        *,
        authorization: str | None,
    ) -> DashboardEvolucaoResponse:
        ...
