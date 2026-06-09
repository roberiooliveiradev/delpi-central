from __future__ import annotations

from app.application.dto.lmp.lmp_dashboard_summary_response import (
    LMPDashboardSummaryResponse,
)
from app.domain.services.query_cache_stats_service import record_cache_get, record_cache_set
from app.infrastructure.cache.ttl_cache import TtlCache

_LMP_DASHBOARD_SUMMARY_TTL_SECONDS = 300.0

_lmp_dashboard_summary_cache: TtlCache[LMPDashboardSummaryResponse] = TtlCache(
    ttl_seconds=_LMP_DASHBOARD_SUMMARY_TTL_SECONDS,
)


def lmp_dashboard_summary_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
    include_avg_lead_time: bool,
    include_qtd_pi: bool,
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
) -> LMPDashboardSummaryResponse | None:
    cached = _lmp_dashboard_summary_cache.get(key)
    record_cache_get(key, hit=cached is not None)
    return cached


def set_cached_lmp_dashboard_summary(
    key: str,
    value: LMPDashboardSummaryResponse,
) -> None:
    _lmp_dashboard_summary_cache.set(key, value)
    record_cache_set(key)
