from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_query_settings import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    MAX_PAGE_SIZE,
)

VALID_SORT_BY = frozenset({"data", "horas", "custo"})
VALID_SORT_DIR = frozenset({"asc", "desc"})


@dataclass(frozen=True, slots=True)
class RetrabalhoDetalhesRequest:
    query: RetrabalhoQueryRequest
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = DEFAULT_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR

    @classmethod
    def from_query(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        order_by: str | None = None,
        order_dir: str | None = None,
    ) -> RetrabalhoDetalhesRequest:
        base = RetrabalhoQueryRequest.from_query(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        normalized_sort_by = str(order_by or DEFAULT_SORT_BY).strip().lower() or DEFAULT_SORT_BY
        normalized_sort_dir = str(order_dir or DEFAULT_SORT_DIR).strip().lower() or DEFAULT_SORT_DIR

        if normalized_sort_by not in VALID_SORT_BY:
            raise ValueError('orderBy inválido. Use "data", "horas" ou "custo".')
        if normalized_sort_dir not in VALID_SORT_DIR:
            raise ValueError('orderDir inválido. Use "asc" ou "desc".')

        return cls(
            query=base,
            page=page,
            page_size=page_size,
            sort_by=normalized_sort_by,
            sort_dir=normalized_sort_dir,
        )

    def resolve_page(self) -> int:
        return max(int(self.page), 1)

    def resolve_page_size(self) -> int:
        return min(max(int(self.page_size), 1), MAX_PAGE_SIZE)

    def periodo_dict(self) -> dict[str, str]:
        return self.query.periodo_dict()
