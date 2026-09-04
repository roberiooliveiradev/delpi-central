"""FastAPI Query factories backed by pagination_tiers.json."""

from __future__ import annotations

from typing import Any

from fastapi import Query

from app.domain.services.pagination_tier_service import PaginationTierService


def _query_for_tier(tier_id: str, *, description: str | None = None) -> Any:
    tier = PaginationTierService.get(tier_id)
    kwargs: dict[str, Any] = {"ge": tier.ge}
    if tier.le is not None:
        kwargs["le"] = tier.le
    if description:
        kwargs["description"] = description
    elif tier.description:
        kwargs["description"] = tier.description
    return Query(tier.default, **kwargs)


def PAGE_SIZE_QUERY(tier_id: str = "page_50_200", *, description: str | None = None) -> Any:
    """Factory for ``page_size`` Query params."""
    return _query_for_tier(tier_id, description=description)


def LIMIT_QUERY(tier_id: str = "limit_optional_200", *, description: str | None = None) -> Any:
    """Factory for ``limit`` Query params."""
    return _query_for_tier(tier_id, description=description)


def TOP_LIMIT_QUERY(tier_id: str = "top_limit_5_20", *, description: str | None = None) -> Any:
    """Factory for ``top_limit`` Query params."""
    return _query_for_tier(tier_id, description=description)


def HISTORY_LIMIT_QUERY(
    tier_id: str = "history_limit_optional_200", *, description: str | None = None
) -> Any:
    """Factory for ``history_limit`` Query params."""
    return _query_for_tier(tier_id, description=description)


def PAGE_50_200(*, description: str | None = None) -> Any:
    return PAGE_SIZE_QUERY("page_50_200", description=description)


def PAGE_50_500(*, description: str | None = None) -> Any:
    return PAGE_SIZE_QUERY("page_50_500", description=description)


def PAGE_20_100(*, description: str | None = None) -> Any:
    return PAGE_SIZE_QUERY("page_20_100", description=description)


def PAGE_OPTIONAL_500(*, description: str | None = None) -> Any:
    return PAGE_SIZE_QUERY("page_optional_500", description=description)


def DETAILS_LIMIT_QUERY(tier_id: str = "details_limit_20_100", *, description: str | None = None):
    """Factory for ``details_limit`` Query params."""
    return _query_for_tier(tier_id, description=description)
