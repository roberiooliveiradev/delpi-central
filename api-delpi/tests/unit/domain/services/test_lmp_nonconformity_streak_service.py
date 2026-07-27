"""Unit — streak dias sem NC LMP."""

from __future__ import annotations

from datetime import date

from app.domain.services.lmp.lmp_nonconformity_streak_service import (
    compute_lmp_nc_streak,
)


def test_streak_empty_without_reference() -> None:
    result = compute_lmp_nc_streak([], as_of=date(2026, 7, 27))
    assert result["current_days_without_nc"] == 0
    assert result["record_days_without_nc"] == 0
    assert result["last_nc_date"] is None
    assert result["reference_start_date"] is None
    assert result["nc_count"] == 0


def test_streak_empty_uses_first_ov_reference() -> None:
    result = compute_lmp_nc_streak(
        [],
        as_of=date(2026, 7, 27),
        reference_start_date=date(2026, 1, 1),
    )
    assert result["current_days_without_nc"] == 207
    assert result["record_days_without_nc"] == 207
    assert result["last_nc_date"] is None
    assert result["reference_start_date"] == "2026-01-01"
    assert result["nc_count"] == 0


def test_streak_current_and_record_gap() -> None:
    # NC em 01/01 e 26/02 → gap 56; as_of 27/02 → current 1; record max(1, 56)=56
    # Ajuste: gap 01/01 → 25/02 = 55 dias (recorde do cartaz)
    result = compute_lmp_nc_streak(
        [date(2026, 1, 1), date(2026, 2, 25)],
        as_of=date(2026, 2, 26),
    )
    assert result["last_nc_date"] == "2026-02-25"
    assert result["current_days_without_nc"] == 1
    assert result["record_days_without_nc"] == 55


def test_streak_resets_on_same_day() -> None:
    result = compute_lmp_nc_streak(
        [date(2026, 7, 27)],
        as_of=date(2026, 7, 27),
    )
    assert result["current_days_without_nc"] == 0
    assert result["record_days_without_nc"] == 0


def test_streak_current_becomes_record() -> None:
    result = compute_lmp_nc_streak(
        [date(2026, 1, 1)],
        as_of=date(2026, 3, 1),
    )
    # 2026-03-01 - 2026-01-01 = 59
    assert result["current_days_without_nc"] == 59
    assert result["record_days_without_nc"] == 59
