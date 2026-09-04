# app/infrastructure/persistence/totvs/pagination.py
"""Offset pagination helpers — max page size comes from a named tier."""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService

_INFRA_TIER = "infra_offset_50_1000"


def default_page_size(*, tier_id: str = _INFRA_TIER) -> int:
    return int(PaginationTierService.require_int(tier_id, None))


def max_page_size(*, tier_id: str = _INFRA_TIER) -> int:
    le = PaginationTierService.max_size(tier_id)
    return int(le if le is not None else 1000)


# Back-compat aliases (prefer PaginationTierService / route tier).
DEFAULT_PAGE_SIZE = default_page_size()
MAX_PAGE_SIZE = max_page_size()


def paginate(page: int, page_size: int, *, max_page_size: int | None = None, tier_id: str = _INFRA_TIER):
    page = max(page or 1, 1)

    cap = int(max_page_size) if max_page_size is not None else PaginationTierService.max_size(tier_id)
    if cap is None:
        cap = 1000

    if page_size is None or page_size == 0:
        page_size = PaginationTierService.require_int(tier_id, None)
    else:
        page_size = int(page_size)

    page_size = min(max(page_size, 1), int(cap))

    offset = (page - 1) * page_size

    return {
        "page": page,
        "page_size": page_size,
        "offset": offset,
    }


def build_page_response(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }
