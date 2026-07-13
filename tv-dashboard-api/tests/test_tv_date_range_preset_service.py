from __future__ import annotations

from datetime import date

from tv_app.application.services.tv_date_range_preset_service import (
    apply_date_range_preset,
    compute_preset_range,
    find_date_range_keys,
)


def test_find_date_range_keys_prefers_schema_names():
    assert find_date_range_keys(["date_start", "date_end", "branch"]) == ("date_start", "date_end")
    assert find_date_range_keys(["start_date", "end_date"]) == ("start_date", "end_date")
    assert find_date_range_keys(["branch"]) is None


def test_this_month_and_this_week(today_fixed: date | None = None):
    today = today_fixed or date(2026, 7, 13)  # segunda
    assert compute_preset_range("this_month", today=today) == (date(2026, 7, 1), today)
    assert compute_preset_range("this_week", today=today) == (date(2026, 7, 13), today)
    assert compute_preset_range("today", today=today) == (today, today)
    assert compute_preset_range("last_7_days", today=today) == (date(2026, 7, 7), today)
    assert compute_preset_range("last_n_days", period_days=10, today=today) == (
        date(2026, 7, 4),
        today,
    )
    assert compute_preset_range("custom", today=today) is None


def test_apply_preset_writes_schema_keys_and_strips_internal():
    today = date(2026, 7, 13)
    out = apply_date_range_preset(
        {"dateRangePreset": "this_month", "branch": "01", "status": "Todos"},
        schema_keys=["date_start", "date_end", "branch", "status"],
        today=today,
    )
    assert out["date_start"] == "2026-07-01"
    assert out["date_end"] == "2026-07-13"
    assert out["branch"] == "01"
    assert "dateRangePreset" not in out
    assert "start_date" not in out


def test_apply_preset_does_not_mirror_aliases():
    today = date(2026, 7, 13)
    out = apply_date_range_preset(
        {"dateRangePreset": "this_month"},
        schema_keys=["date_start", "date_end"],
        today=today,
    )
    assert out["date_start"] == "2026-07-01"
    assert "start_date" not in out
    assert "end_date" not in out


def test_custom_keeps_manual_dates():
    out = apply_date_range_preset(
        {
            "dateRangePreset": "custom",
            "date_start": "2026-01-01",
            "date_end": "2026-01-31",
        },
        schema_keys=["date_start", "date_end"],
        today=date(2026, 7, 13),
    )
    assert out["date_start"] == "2026-01-01"
    assert out["date_end"] == "2026-01-31"
