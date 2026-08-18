"""Bucket open-order lines by promised delivery date (KPI-CARTEIRA-HORIZON)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

HORIZON_TIMEZONE = "America/Sao_Paulo"
NATURE_OPEN_ORDER_VALUE_BY_DELIVERY = "open_order_value_by_delivery"

BUCKET_OVERDUE = "overdue"
BUCKET_CURRENT_MONTH = "current_month"
BUCKET_NEXT_1_3_MONTHS = "next_1_3_months"
BUCKET_LATER = "later"
BUCKET_UNDATED = "undated"

BUCKET_IDS: tuple[str, ...] = (
    BUCKET_OVERDUE,
    BUCKET_CURRENT_MONTH,
    BUCKET_NEXT_1_3_MONTHS,
    BUCKET_LATER,
    BUCKET_UNDATED,
)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_delivery_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + delta
    return idx // 12, idx % 12 + 1


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _month_end(year: int, month: int) -> date:
    y2, m2 = _add_months(year, month, 1)
    return _month_start(y2, m2) - timedelta(days=1)


def delivery_windows(as_of_date: date) -> tuple[date, date, date, date]:
    """Current month start/end and next-1-to-3-months start/end."""
    cy, cm = as_of_date.year, as_of_date.month
    current_start = _month_start(cy, cm)
    current_end = _month_end(cy, cm)
    n1_y, n1_m = _add_months(cy, cm, 1)
    n3_y, n3_m = _add_months(cy, cm, 3)
    return (
        current_start,
        current_end,
        _month_start(n1_y, n1_m),
        _month_end(n3_y, n3_m),
    )


def _empty_bucket(bucket_id: str) -> dict[str, Any]:
    return {"id": bucket_id, "openValue": 0.0, "openLineCount": 0}


class OpenOrdersHorizonBucketService:
    """Pure bucketing of open-order lines by data_entrega (America/Sao_Paulo)."""

    def bucketize(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        as_of: datetime | None = None,
        timezone_name: str = HORIZON_TIMEZONE,
    ) -> dict[str, Any]:
        tz = ZoneInfo(timezone_name)
        stamp = as_of or datetime.now(tz)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=tz)
        else:
            stamp = stamp.astimezone(tz)
        as_of_date = stamp.date()
        buckets = {bid: _empty_bucket(bid) for bid in BUCKET_IDS}
        current_start, current_end, next_start, next_end = delivery_windows(as_of_date)

        rows = items or ()
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            value = _as_float(row.get("valor_aberto"))
            bucket_id = self.resolve_bucket_id(
                row,
                as_of_date=as_of_date,
                current_start=current_start,
                current_end=current_end,
                next_start=next_start,
                next_end=next_end,
            )

            bucket = buckets[bucket_id]
            bucket["openValue"] = float(bucket["openValue"]) + value
            bucket["openLineCount"] = int(bucket["openLineCount"]) + 1

        ordered = [buckets[bid] for bid in BUCKET_IDS]
        totals = {
            "openValue": sum(float(b["openValue"]) for b in ordered),
            "openLineCount": sum(int(b["openLineCount"]) for b in ordered),
        }
        return {
            "asOf": stamp.isoformat(),
            "timezone": timezone_name,
            "nature": NATURE_OPEN_ORDER_VALUE_BY_DELIVERY,
            "buckets": ordered,
            "totals": totals,
        }

    def resolve_bucket_id(
        self,
        item: Mapping[str, Any],
        *,
        as_of_date: date,
        current_start: date,
        current_end: date,
        next_start: date,
        next_end: date,
    ) -> str:
        delivery = _parse_delivery_date(item.get("data_entrega"))
        if delivery is None:
            return BUCKET_UNDATED
        if delivery < as_of_date:
            return BUCKET_OVERDUE
        if current_start <= delivery <= current_end:
            return BUCKET_CURRENT_MONTH
        if next_start <= delivery <= next_end:
            return BUCKET_NEXT_1_3_MONTHS
        return BUCKET_LATER

