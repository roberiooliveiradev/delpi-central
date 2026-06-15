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
        sort_by: str | None = None,
        sort_dir: str | None = None,
        incluir_bloqueados: bool | None = None,
    ) -> dict:
        return self._client.list_mini_applicators_ferramentas(
            params={
                "codigo": codigo,
                "descricao": descricao,
                "filial": filial,
                "page": str(page) if page is not None else None,
                "page_size": str(page_size) if page_size is not None else None,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "incluir_bloqueados": "true" if incluir_bloqueados else None,
            },
            authorization=bearer_authorization_from_context(),
        )

    def obter_ferramenta(self, codigo: str) -> dict:
        return self._client.get_mini_applicators_ferramenta(
            codigo,
            authorization=bearer_authorization_from_context(),
        )

    def listar_pecas(self, codigo_ferramenta: str) -> dict:
        return self._client.list_mini_applicators_pecas(
            codigo_ferramenta,
            authorization=bearer_authorization_from_context(),
        )

    def obter_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict:
        return self._client.get_mini_applicators_golpes(
            codigo_ferramenta,
            params={
                "filial": filial,
                "data_inicial": data_inicial,
                "data_final": data_final,
            },
            authorization=bearer_authorization_from_context(),
        )

    def listar_componentes(self, *, codigo_ferramenta: str, filial: str) -> dict:
        return self._client.list_mini_applicators_componentes(
            codigo_ferramenta,
            params={"filial": filial},
            authorization=bearer_authorization_from_context(),
        )
