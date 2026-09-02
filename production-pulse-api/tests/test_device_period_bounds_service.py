from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from production_pulse_app.domain.services.device_period_bounds_service import (
    resolve_day_bounds,
    resolve_shift_bounds,
)


def test_resolve_day_bounds_uses_local_midnight():
    tz = ZoneInfo("America/Sao_Paulo")
    local = datetime(2026, 9, 1, 15, 30, tzinfo=tz)
    now = local.astimezone(timezone.utc)
    start, end = resolve_day_bounds(now, tz_name="America/Sao_Paulo")

    assert start.astimezone(tz).hour == 0
    assert end.astimezone(tz).day == 2
    assert (end - start).total_seconds() == 86400


def test_resolve_shift_bounds_morning_window():
    tz = ZoneInfo("America/Sao_Paulo")
    local = datetime(2026, 9, 1, 8, 0, tzinfo=tz)
    start, end = resolve_shift_bounds(local.astimezone(timezone.utc), tz_name="America/Sao_Paulo")

    assert start.astimezone(tz).hour == 6
    assert end.astimezone(tz).hour == 14


def test_resolve_shift_bounds_night_window_after_midnight():
    tz = ZoneInfo("America/Sao_Paulo")
    local = datetime(2026, 9, 2, 2, 0, tzinfo=tz)
    start, end = resolve_shift_bounds(local.astimezone(timezone.utc), tz_name="America/Sao_Paulo")

    assert start.astimezone(tz).day == 1
    assert start.astimezone(tz).hour == 22
    assert end.astimezone(tz).day == 2
    assert end.astimezone(tz).hour == 6
