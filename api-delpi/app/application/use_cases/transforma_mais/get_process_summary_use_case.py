from __future__ import annotations

from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse
from app.domain.ports.transforma_mais.integration_port import TransformaMaisIntegrationPort
from app.infrastructure.http.auth_header import bearer_authorization_from_context


class GetProcessSummaryUseCase:
    def __init__(self, gateway: TransformaMaisIntegrationPort):
        self._gateway = gateway

    def execute(self, request: ProcessSummaryRequest) -> ProcessSummaryResponse:
        return self._gateway.get_summary(
            request,
            authorization=bearer_authorization_from_context(),
        )
