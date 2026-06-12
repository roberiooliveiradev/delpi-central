from __future__ import annotations

from delpi_api_client import DelpiApiClient

from maint_app.infrastructure.http.auth_header import bearer_authorization_from_context


class DelpiMiniAplicatorsGateway:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def listar_ferramentas(
        self,
        *,
        codigo: str | None = None,
        descricao: str | None = None,
        filial: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict:
        return self._client.list_mini_applicators_ferramentas(
            params={
                "codigo": codigo,
                "descricao": descricao,
                "filial": filial,
                "page": str(page) if page is not None else None,
                "page_size": str(page_size) if page_size is not None else None,
            },
            authorization=bearer_authorization_from_context(),
        )

    def obter_ferramenta(self, codigo: str) -> dict:
        return self._client.get_mini_applicators_ferramenta(
            codigo,
            authorization=bearer_authorization_from_context(),
        )
