from __future__ import annotations

from si_app.application.services.engineering.engineering_lmp_summary_cache import (
    get_cached_lmp_summary,
    lmp_summary_cache_key,
    set_cached_lmp_summary,
)


def resolve_lmp_dashboard_summary(
    *,
    gateway,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
) -> dict[str, float | int]:
    cache_key = lmp_summary_cache_key(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
    )
    cached = get_cached_lmp_summary(cache_key)
    if cached is not None:
        return cached

    response = gateway.get_lmp_dashboard_summary(
        date_start=date_start,
        date_end=date_end,
        branch=branch,
    )
    set_cached_lmp_summary(cache_key, response)
    return response
