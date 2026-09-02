from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from production_pulse_app.infrastructure.content.period_aggregation_content_service import (
    period_shift_windows,
    period_timezone_name,
)


def _localize(now: datetime, tz: ZoneInfo) -> datetime:
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc).astimezone(tz)
    return now.astimezone(tz)


def resolve_day_bounds(now: datetime, *, tz_name: str | None = None) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name or period_timezone_name())
    local = _localize(now, tz)
    start_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _shift_window_for_local_time(
    local: datetime,
    *,
    start_hour: int,
    end_hour: int,
) -> tuple[datetime, datetime] | None:
    start_local = local.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_local = local.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    minute_of_day = local.hour * 60 + local.minute
    start_minute = start_hour * 60
    end_minute = end_hour * 60

    if start_minute < end_minute:
        if not (start_minute <= minute_of_day < end_minute):
            return None
        return start_local, end_local

    if minute_of_day >= start_minute:
        end_local = end_local + timedelta(days=1)
        return start_local, end_local

    if minute_of_day < end_minute:
        start_local = start_local - timedelta(days=1)
        return start_local, end_local

    return None


def resolve_shift_bounds(now: datetime, *, tz_name: str | None = None) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name or period_timezone_name())
    local = _localize(now, tz)

    for shift in period_shift_windows():
        try:
            start_hour = int(shift.get("startHour"))
            end_hour = int(shift.get("endHour"))
        except (TypeError, ValueError):
            continue

        window = _shift_window_for_local_time(
            local,
            start_hour=start_hour,
            end_hour=end_hour,
        )
        if window is not None:
            start_local, end_local = window
            return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    return resolve_day_bounds(now, tz_name=tz.key)


__all__ = ["resolve_day_bounds", "resolve_shift_bounds"]
