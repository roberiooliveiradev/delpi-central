from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from app.application.dto.lmp.lmp_dashboard_summary_response import (
    LMPDashboardSummaryResponse,
)
from app.composition.query_cache_composer import build_query_cache

T = TypeVar("T")


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
    cached = build_query_cache().get(key)
    if isinstance(cached, LMPDashboardSummaryResponse):
        return cached
    if isinstance(cached, dict):
        try:
            return LMPDashboardSummaryResponse(**cached)
        except TypeError:
            return None
    return None


def set_cached_lmp_dashboard_summary(
    key: str,
    value: LMPDashboardSummaryResponse,
) -> None:
    build_query_cache().set(key, value.to_dict())


def get_or_set_cached_lmp_dashboard_summary(
    key: str,
    factory: Callable[[], LMPDashboardSummaryResponse],
) -> LMPDashboardSummaryResponse:
    def compute() -> dict:
        return factory().to_dict()

    value = build_query_cache().get_or_set(key, compute)
    if isinstance(value, LMPDashboardSummaryResponse):
        return value
    if isinstance(value, dict):
        return LMPDashboardSummaryResponse(**value)
    return factory()
