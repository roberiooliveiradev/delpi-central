from __future__ import annotations

from typing import Protocol


class InadimplenciaRepositoryPort(Protocol):
    def get_resumo(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
    ) -> dict: ...

    def get_mensal(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        customer_pairs: tuple[tuple[str, str], ...] | None = None,
        novos_negocios: bool = False,
    ) -> list[dict]: ...

    def get_faixas_atraso(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
    ) -> list[dict]: ...

    def count_clientes(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        q: str | None = None,
        only_with_delays: bool = True,
    ) -> int: ...

    def list_clientes(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        q: str | None = None,
        only_with_delays: bool = True,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def count_titulos(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        status: str = "all",
        delay_range: str | None = None,
        q: str | None = None,
    ) -> int: ...

    def list_titulos(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        status: str = "all",
        delay_range: str | None = None,
        q: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]: ...
