from __future__ import annotations

from si_app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from si_app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse
from si_app.domain.ports.transforma_mais.integration_port import TransformaMaisIntegrationPort
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context


class GetProcessSummaryUseCase:
    def __init__(self, gateway: TransformaMaisIntegrationPort):
        self._gateway = gateway

    def execute(self, request: ProcessSummaryRequest) -> ProcessSummaryResponse:
        return self._gateway.get_summary(
            request,
            authorization=bearer_authorization_from_context(),
        )
