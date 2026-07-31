"""Envelope paged_list genérico (page / total / pagination.is_complete)."""

from __future__ import annotations

from typing import Any


def build_paged_list_envelope(
    *,
    page: int,
    page_size: int,
    total: int,
    items: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    total_pages = (total + page_size - 1) // page_size if total else 0
    payload: dict[str, Any] = {
        "items": items,
        "page": page,
        "page_size": page_size,
        "pageSize": page_size,
        "total": total,
        "total_pages": total_pages,
        "totalPages": total_pages,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "is_complete": page >= total_pages if total_pages else True,
        },
    }
    if extra:
        payload.update(extra)
    return payload
