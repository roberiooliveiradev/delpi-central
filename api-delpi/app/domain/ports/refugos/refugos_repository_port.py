from __future__ import annotations

from typing import Protocol


class RefugosRepositoryPort(Protocol):
    def check_health(self) -> dict: ...

    def get_filtros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
    ) -> dict: ...

    def get_resumo(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        day_start: str,
        day_end_exclusive: str,
        month_start: str,
        month_end_exclusive: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> dict: ...

    def get_ranking(
        self,
        *,
        dimension: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        limit: int,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]: ...

    def get_serie(
        self,
        *,
        granularity: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]: ...

    def get_registros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        offset: int,
        page_size: int,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]: ...

    def count_registros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> int: ...
