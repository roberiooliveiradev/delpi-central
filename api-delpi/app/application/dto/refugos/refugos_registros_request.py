from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)


@dataclass(frozen=True, slots=True)
class RefugosRegistrosRequest:
    query: RefugosQueryRequest
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_query(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> RefugosRegistrosRequest:
        query = RefugosQueryRequest.from_query(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        return cls(
            query=query,
            page=max(int(page or DEFAULT_PAGE), 1),
            page_size=min(max(int(page_size or DEFAULT_PAGE_SIZE), 1), MAX_PAGE_SIZE),
        )

    def resolve_page(self) -> int:
        return self.page

    def resolve_page_size(self) -> int:
        return self.page_size

    def periodo_dict(self) -> dict[str, str]:
        return self.query.periodo_dict()
