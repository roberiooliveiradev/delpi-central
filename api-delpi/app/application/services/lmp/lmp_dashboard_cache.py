from __future__ import annotations

from typing import Any

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


def get_cached_lmp_dashboard(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_lmp_dashboard(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)


def invalidate_lmp_dashboard_cache() -> None:
    build_query_cache().invalidate_all()
