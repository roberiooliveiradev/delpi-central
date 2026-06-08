from __future__ import annotations

from si_app.config import settings
from si_app.infrastructure.cache.ttl_cache import TtlCache

_lmp_dashboard_summary_cache: TtlCache[dict[str, float | int]] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)


def lmp_dashboard_summary_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    include_avg_lead_time: bool,
    include_qtd_pi: bool = False,
) -> str:
    return "|".join(
        [
            "lmp-summary",
            date_start or "",
            date_end or "",
            branch or "",
            "1" if include_avg_lead_time else "0",
            "1" if include_qtd_pi else "0",
        ]
    )


def get_cached_lmp_dashboard_summary(
    key: str,
) -> dict[str, float | int] | None:
    return _lmp_dashboard_summary_cache.get(key)


def set_cached_lmp_dashboard_summary(
    key: str,
    value: dict[str, float | int],
) -> None:
    _lmp_dashboard_summary_cache.set(key, value)


def invalidate_lmp_dashboard_summary_cache() -> None:
    _lmp_dashboard_summary_cache.invalidate_all()
