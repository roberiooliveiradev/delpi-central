from __future__ import annotations

from typing import Protocol

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse
from app.domain.entities.transforma_mais.process import Process


class TransformaMaisIntegrationPort(Protocol):
    def list_processes(self, request: ProcessRequest, *, authorization: str | None) -> list[Process]:
        ...

    def get_summary(
        self,
        request: ProcessSummaryRequest,
        *,
        authorization: str | None,
    ) -> ProcessSummaryResponse:
        ...
