from __future__ import annotations

from typing import Protocol


class RetrabalhoRepositoryPort(Protocol):
    def check_health(self) -> dict: ...

    def get_filtros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
    ) -> dict: ...

    def get_resumo(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict: ...

    def get_top_recurso(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict | None: ...

    def get_top_colaborador(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict | None: ...

    def get_mensal(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> list[dict]: ...

    def get_ranking_recursos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        order_by: str = "horas",
        limit: int = 10,
    ) -> list[dict]: ...

    def get_ranking_colaboradores(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        order_by: str = "horas",
        limit: int = 10,
    ) -> list[dict]: ...

    def get_detalhes(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        sort_by: str = "data",
        sort_dir: str = "desc",
        offset: int = 0,
        page_size: int = 50,
    ) -> list[dict]: ...

    def count_detalhes(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> int: ...
