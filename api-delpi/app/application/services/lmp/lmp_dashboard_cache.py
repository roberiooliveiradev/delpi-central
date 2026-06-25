from __future__ import annotations

from typing import Any

from app.application.dto.lmp.list_lmp_request import resolve_listing_type_filter
from app.composition.query_cache_composer import build_query_cache


def lmp_dashboard_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    listing_type: str | None,
    status_filter: str,
) -> str:
    return "|".join(
        [
            "lmp-dashboard",
            date_start or "",
            date_end or "",
            branch or "",
            listing_type or "",
            status_filter or "Todos",
        ]
    )


def get_cached_lmp_dashboard(key: str) -> Any | None:
    return build_query_cache().get(key)


def set_cached_lmp_dashboard(key: str, value: Any) -> None:
    build_query_cache().set(key, value)


def invalidate_lmp_dashboard_cache() -> None:
    build_query_cache().invalidate_all()


def lmp_dashboard_summary_rows_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    listing_type: str | None,
    include_qtd_pi: bool,
) -> str:
    listing = resolve_listing_type_filter(listing_type) or "Todos"
    return "|".join(
        [
            "lmp-dashboard-summary-rows",
            date_start or "",
            date_end or "",
            branch or "",
            listing,
            "1" if include_qtd_pi else "0",
        ]
    )


def get_cached_lmp_dashboard_summary_rows(key: str) -> list[dict[str, Any]] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_lmp_dashboard_summary_rows(
    key: str,
    value: list[dict[str, Any]],
) -> None:
    build_query_cache().set(key, value)
