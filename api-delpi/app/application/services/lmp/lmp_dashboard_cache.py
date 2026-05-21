from __future__ import annotations

from typing import Any

from app.infrastructure.cache.ttl_cache import TtlCache

_LMP_DASHBOARD_TTL_SECONDS = 120.0

_lmp_dashboard_cache: TtlCache[dict[str, Any]] = TtlCache(
    ttl_seconds=_LMP_DASHBOARD_TTL_SECONDS,
)


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
    return _lmp_dashboard_cache.get(key)


def set_cached_lmp_dashboard(key: str, value: dict[str, Any]) -> None:
    _lmp_dashboard_cache.set(key, value)


def invalidate_lmp_dashboard_cache() -> None:
    _lmp_dashboard_cache.invalidate_all()
