"""Typed request for financial settlement event queries (FK1/FK2).

Scope of the contract (doc 48 §9/§11 — D3.1): no ``branch`` parameter is
accepted. No Protheus column proved to carry the business branch, and an
empty ``*_FILIAL`` must not be interpreted as authorized scope.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

from .constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    SORTABLE_FIELDS,
)

SORT_DIRECTIONS = frozenset({"asc", "desc"})


@dataclass(frozen=True, slots=True)
class SettlementsQueryRequest:
    start_date: str
    end_date: str
    nature_code: str | None = None
    movement_type: str | None = None
    sort_by: str = DEFAULT_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None,
        end_date: str | None,
        nature_code: str | None = None,
        movement_type: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> "SettlementsQueryRequest":
        normalized_start = str(start_date or "").strip()
        normalized_end = str(end_date or "").strip()
        if not normalized_start or not normalized_end:
            raise ValueError("start_date e end_date são obrigatórios.")

        resolved_sort_by = (sort_by or DEFAULT_SORT_BY).strip().lower()
        if resolved_sort_by not in SORTABLE_FIELDS:
            raise ValueError(
                "sort_by inválido. Valores aceitos: " + ", ".join(sorted(SORTABLE_FIELDS))
            )
        resolved_sort_dir = (sort_dir or DEFAULT_SORT_DIR).strip().lower()
        if resolved_sort_dir not in SORT_DIRECTIONS:
            raise ValueError("sort_dir inválido. Use asc ou desc.")

        request = cls(
            start_date=normalized_start,
            end_date=normalized_end,
            nature_code=(nature_code or "").strip() or None,
            movement_type=(movement_type or "").strip() or None,
            sort_by=resolved_sort_by,
            sort_dir=resolved_sort_dir,
            page=max(int(page or DEFAULT_PAGE), 1),
            page_size=int(page_size or DEFAULT_PAGE_SIZE),
        )
        # Malformed input must fail before any authorization/scope gate —
        # a 400 never depends on dataset access.
        request.resolve_protheus_period()
        return request

    def resolve_protheus_period(self) -> tuple[str, str]:
        """Inclusive YYYYMMDD bounds for ``FKx_DATA`` filtering."""
        qb = QueryBuilder()
        start = qb.convert_date_to_protheus(self.start_date)
        end = qb.convert_date_to_protheus(self.end_date)
        if not start:
            raise ValueError(
                "start_date inválida. Use formatos como YYYYMMDD ou YYYY-MM-DD."
            )
        if not end:
            raise ValueError(
                "end_date inválida. Use formatos como YYYYMMDD ou YYYY-MM-DD."
            )
        if start > end:
            raise ValueError("start_date não pode ser maior que end_date.")
        return start, end
