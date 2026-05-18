from __future__ import annotations

from si_app.application.dto.lmp.lmp_dashboard_summary_response import (
    LMPDashboardSummaryResponse,
)
from si_app.config import settings
from si_app.infrastructure.cache.ttl_cache import TtlCache

_lmp_dashboard_summary_cache: TtlCache[LMPDashboardSummaryResponse] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)


def lmp_dashboard_summary_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    include_avg_lead_time: bool,
) -> str:
    return "|".join(
        [
            "lmp-summary",
            date_start or "",
            date_end or "",
            branch or "",
            "1" if include_avg_lead_time else "0",
        ]
    )


def get_cached_lmp_dashboard_summary(
    key: str,
) -> LMPDashboardSummaryResponse | None:
    return _lmp_dashboard_summary_cache.get(key)


def set_cached_lmp_dashboard_summary(
    key: str,
    value: LMPDashboardSummaryResponse,
) -> None:
    _lmp_dashboard_summary_cache.set(key, value)


def invalidate_lmp_dashboard_summary_cache() -> None:
    _lmp_dashboard_summary_cache.invalidate_all()
