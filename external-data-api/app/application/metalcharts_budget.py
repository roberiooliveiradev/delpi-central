"""MetalCharts Free-plan allowance guard (PROC-0076 R5).

Server-side accounting of the upstream weight budget: every call is
charged to ``source_api_call_ledger`` BEFORE the upstream request, and
both the monthly window (account allowance) and the per-minute window
(key limit) must have headroom — a burst of portal users or a racing
job can never burn the whole allowance.

The ledger's per-minute unique index collapses an exact retry, and the
budget deliberately sits BELOW the published plan limits
(``METALCHARTS_MONTHLY_WEIGHT_BUDGET`` /
``METALCHARTS_MINUTE_WEIGHT_BUDGET``) so homologation and manual
recovery keep a reserve.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.application.contracts import RateLimitedError
from app.domain.market_data import PROVIDER_METALCHARTS
from app.infrastructure.config.settings import Settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MetalChartsBudget:
    """Check-then-record allowance gate for upstream MetalCharts calls."""

    def __init__(
        self,
        *,
        repository: Any,
        monthly_budget: int | None = None,
        minute_budget: int | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repo = repository
        self._monthly_budget = (
            monthly_budget
            if monthly_budget is not None
            else Settings.METALCHARTS_MONTHLY_WEIGHT_BUDGET
        )
        self._minute_budget = (
            minute_budget
            if minute_budget is not None
            else Settings.METALCHARTS_MINUTE_WEIGHT_BUDGET
        )
        self._clock = clock or utcnow

    def acquire(self, *, weight: int) -> None:
        """Raise ``RateLimitedError`` unless both windows have headroom
        for ``weight`` units — no upstream call is made otherwise."""
        now = self._clock()
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        minute_start = now - timedelta(minutes=1)
        used_month = self._repo.sum_api_call_weight(
            source_id=PROVIDER_METALCHARTS, since=month_start
        )
        if used_month + weight > self._monthly_budget:
            raise RateLimitedError(
                "metalcharts monthly allowance budget exhausted"
            )
        used_minute = self._repo.sum_api_call_weight(
            source_id=PROVIDER_METALCHARTS, since=minute_start
        )
        if used_minute + weight > self._minute_budget:
            raise RateLimitedError(
                "metalcharts per-minute allowance budget exhausted",
                retry_after=60,
            )

    def record(
        self,
        *,
        endpoint: str,
        params_key: str,
        weight: int,
        http_status: int | None,
        correlation_id: str | None,
    ) -> bool:
        """Charge the call to the ledger; False when the ledger dedups
        an identical call inside the same minute (already charged)."""
        return self._repo.record_api_call(
            source_id=PROVIDER_METALCHARTS,
            endpoint=endpoint,
            params_hash=params_key,
            weight=weight,
            http_status=http_status,
            correlation_id=correlation_id,
        )
