from __future__ import annotations

from typing import List

from si_app.application.dto.transforma_mais.process_request import ProcessRequest
from si_app.domain.entities.transforma_mais.process import Process
from si_app.domain.ports.transforma_mais.integration_port import TransformaMaisIntegrationPort
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context


class ListProcessUseCase:
    def __init__(self, gateway: TransformaMaisIntegrationPort):
        self._gateway = gateway

    def execute(self, request: ProcessRequest) -> List[Process]:
        return self._gateway.list_processes(
            request,
            authorization=bearer_authorization_from_context(),
        )
