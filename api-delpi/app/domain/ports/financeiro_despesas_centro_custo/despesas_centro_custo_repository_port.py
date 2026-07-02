from __future__ import annotations

from typing import Protocol


class DespesasCentroCustoRepositoryPort(Protocol):
    def get_filtros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
    ) -> dict: ...

    def get_resumo(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
    ) -> dict: ...

    def get_serie(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
    ) -> list[dict]: ...

    def get_ranking_centros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        limit: int = 10,
    ) -> list[dict]: ...

    def get_ranking_fornecedores(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        limit: int = 10,
    ) -> list[dict]: ...

    def count_lancamentos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        search: str | None = None,
    ) -> int: ...

    def list_lancamentos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        search: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]: ...
