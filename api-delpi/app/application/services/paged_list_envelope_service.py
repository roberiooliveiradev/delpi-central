"""Envelope paged_list genérico (page / total / pagination.is_complete)."""

from __future__ import annotations

from typing import Any

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder


def build_has_next_pagination(
    *,
    page: int,
    page_size: int,
    has_next: bool,
) -> dict[str, Any]:
    """Nested pagination when total is unknown (cursor / fetch_next+1)."""
    return PaginationEnvelopeBuilder.has_next(
        page=page,
        page_size=page_size,
        has_next=has_next,
    )


def build_paged_list_envelope(
    *,
    page: int,
    page_size: int,
    total: int,
    items: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pagination = PaginationEnvelopeBuilder.paged_count(
        page=page,
        page_size=page_size,
        total=total,
    )
    total_pages = pagination["total_pages"]
    payload: dict[str, Any] = {
        "items": items,
        "page": page,
        "page_size": page_size,
        "pageSize": page_size,
        "total": total,
        "total_pages": total_pages,
        "totalPages": total_pages,
        "pagination": pagination,
    }
    if extra:
        payload.update(extra)
    return payload
