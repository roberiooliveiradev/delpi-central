"""Classify open-order lines as available vs postponed (no TOTVS postponement field).

Heuristic (documented in padroes-totvs): promised delivery after the current
month = postponed; overdue + current month = available. Undated stays undated.

Reuses KPI-CARTEIRA-HORIZON buckets — does not invent a second calendar.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from commercial_app.domain.services.open_orders_horizon_bucket_service import (
    BUCKET_CURRENT_MONTH,
    BUCKET_LATER,
    BUCKET_NEXT_1_3_MONTHS,
    BUCKET_OVERDUE,
    BUCKET_UNDATED,
    HORIZON_TIMEZONE,
    OpenOrdersHorizonBucketService,
    delivery_windows,
)

AVAILABILITY_AVAILABLE = "available"
AVAILABILITY_POSTPONED = "postponed"
AVAILABILITY_UNDATED = "undated"

_POSTPONED_BUCKETS = frozenset({BUCKET_NEXT_1_3_MONTHS, BUCKET_LATER})
_AVAILABLE_BUCKETS = frozenset({BUCKET_OVERDUE, BUCKET_CURRENT_MONTH})


class OpenOrderAvailabilityClassificationService:
    """Pure availability from delivery-horizon buckets."""

    def __init__(
        self,
        horizon_service: OpenOrdersHorizonBucketService | None = None,
    ) -> None:
        self._horizon = horizon_service or OpenOrdersHorizonBucketService()

    def classify(
        self,
        item: Mapping[str, Any],
        *,
        as_of: datetime | date | None = None,
        timezone_name: str = HORIZON_TIMEZONE,
    ) -> str:
        as_of_date, current_start, current_end, next_start, next_end = self._bounds(
            as_of, timezone_name
        )
        bucket = self._horizon.resolve_bucket_id(
            item,
            as_of_date=as_of_date,
            current_start=current_start,
            current_end=current_end,
            next_start=next_start,
            next_end=next_end,
        )
        if bucket in _POSTPONED_BUCKETS:
            return AVAILABILITY_POSTPONED
        if bucket == BUCKET_UNDATED:
            return AVAILABILITY_UNDATED
        if bucket in _AVAILABLE_BUCKETS:
            return AVAILABILITY_AVAILABLE
        return AVAILABILITY_UNDATED

    def enrich_item(
        self,
        item: Mapping[str, Any],
        *,
        as_of: datetime | date | None = None,
        timezone_name: str = HORIZON_TIMEZONE,
    ) -> dict[str, Any]:
        out = dict(item)
        out["availability"] = self.classify(item, as_of=as_of, timezone_name=timezone_name)
        return out

    def _bounds(
        self,
        as_of: datetime | date | None,
        timezone_name: str,
    ) -> tuple[date, date, date, date, date]:
        tz = ZoneInfo(timezone_name)
        if isinstance(as_of, date) and not isinstance(as_of, datetime):
            as_of_date = as_of
        else:
            stamp = as_of or datetime.now(tz)
            if isinstance(stamp, datetime):
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=tz)
                else:
                    stamp = stamp.astimezone(tz)
                as_of_date = stamp.date()
            else:
                as_of_date = datetime.now(tz).date()
        current_start, current_end, next_start, next_end = delivery_windows(as_of_date)
        return as_of_date, current_start, current_end, next_start, next_end
