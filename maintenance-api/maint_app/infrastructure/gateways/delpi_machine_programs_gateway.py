from __future__ import annotations

from typing import Any

from delpi_api_client import DelpiApiClient

from maint_app.domain.ports.machine_programs_totvs_port import MachineProgramsTotvsPort
from maint_app.infrastructure.http.auth_header import bearer_authorization_from_context


class DelpiMachineProgramsGateway(MachineProgramsTotvsPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def listar_top_intermediates(
        self,
        *,
        filial: str,
        data_inicial: str | None = None,
        data_final: str | None = None,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "branch": filial,
            "page": str(page),
            "page_size": str(page_size),
            "date_start": data_inicial,
            "date_end": data_final,
            "search": search,
        }
        return self._client.list_production_machine_program_top_intermediates(
            params=params,
            authorization=authorization or bearer_authorization_from_context(),
        )
