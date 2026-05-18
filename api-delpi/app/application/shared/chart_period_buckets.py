from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


MAX_PERIOD_BUCKETS = 60


@dataclass(frozen=True)
class PeriodBucket:
    key: str
    label: str
    date_start: str
    date_end: str


@dataclass(frozen=True)
class BuildPeriodBucketsResult:
    buckets: list[PeriodBucket]
    truncated: bool


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _format_iso(d: date) -> str:
    return d.isoformat()


def _format_day_label(iso: str) -> str:
    parsed = date.fromisoformat(iso)
    return parsed.strftime("%d/%m/%y")


def _format_week_label(start_iso: str, end_iso: str) -> str:
    start_label = _format_day_label(start_iso)
    end_label = _format_day_label(end_iso)
    return start_label if start_label == end_label else f"{start_label} – {end_label}"


def _month_key_label(month_key: str) -> str:
    year_str, month_str = month_key.split("-", 1)
    parsed = date(int(year_str), int(month_str), 1)
    return parsed.strftime("%b. de %y").replace(".", ".")


def _clamp_range(
    bucket_start: date,
    bucket_end: date,
    range_start: date,
    range_end: date,
) -> tuple[date, date] | None:
    start = max(bucket_start, range_start)
    end = min(bucket_end, range_end)
    if start > end:
        return None
    return start, end


def build_period_buckets(
    *,
    date_start: str | None,
    date_end: str | None,
    granularity: str,
) -> BuildPeriodBucketsResult:
    if granularity not in {"day", "week", "month", "year"}:
        raise ValueError("granularity deve ser day, week, month ou year")

    range_start = _parse_iso_date(date_start)
    range_end = _parse_iso_date(date_end)

    if not range_start or not range_end or range_start > range_end:
        return BuildPeriodBucketsResult(buckets=[], truncated=False)

    buckets: list[PeriodBucket] = []

    if granularity == "day":
        cursor = range_start
        while cursor <= range_end:
            iso = _format_iso(cursor)
            buckets.append(
                PeriodBucket(
                    key=iso,
                    label=_format_day_label(iso),
                    date_start=iso,
                    date_end=iso,
                )
            )
            cursor += timedelta(days=1)

    elif granularity == "week":
        cursor = range_start - timedelta(days=range_start.weekday())
        while cursor <= range_end:
            bucket_end = cursor + timedelta(days=6)
            clamped = _clamp_range(cursor, bucket_end, range_start, range_end)
            if clamped:
                start_iso = _format_iso(clamped[0])
                end_iso = _format_iso(clamped[1])
                buckets.append(
                    PeriodBucket(
                        key=start_iso,
                        label=_format_week_label(start_iso, end_iso),
                        date_start=start_iso,
                        date_end=end_iso,
                    )
                )
            cursor += timedelta(days=7)

    elif granularity == "month":
        cursor = date(range_start.year, range_start.month, 1)
        while cursor <= range_end:
            last_day = monthrange(cursor.year, cursor.month)[1]
            month_end = date(cursor.year, cursor.month, last_day)
            clamped = _clamp_range(cursor, month_end, range_start, range_end)
            if clamped:
                month_key = f"{clamped[0].year}-{str(clamped[0].month).zfill(2)}"
                buckets.append(
                    PeriodBucket(
                        key=month_key,
                        label=_month_key_label(month_key),
                        date_start=_format_iso(clamped[0]),
                        date_end=_format_iso(clamped[1]),
                    )
                )
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)

    elif granularity == "year":
        for year in range(range_start.year, range_end.year + 1):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            clamped = _clamp_range(year_start, year_end, range_start, range_end)
            if clamped:
                buckets.append(
                    PeriodBucket(
                        key=str(year),
                        label=str(year),
                        date_start=_format_iso(clamped[0]),
                        date_end=_format_iso(clamped[1]),
                    )
                )

    if len(buckets) <= MAX_PERIOD_BUCKETS:
        return BuildPeriodBucketsResult(buckets=buckets, truncated=False)

    return BuildPeriodBucketsResult(
        buckets=buckets[:MAX_PERIOD_BUCKETS],
        truncated=True,
    )
