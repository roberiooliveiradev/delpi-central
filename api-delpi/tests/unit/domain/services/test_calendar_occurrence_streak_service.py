"""Unit — streak de dias sem ocorrência (ignora datas futuras)."""

from __future__ import annotations

from datetime import date

from app.domain.services.calendar_occurrence_streak_service import (
    compute_occurrence_streak,
)


def test_streak_ignores_occurrence_dates_after_as_of() -> None:
    """Regressão TV «Dias sem NC»: QI2_OCORRE futura não pode zerar o indicador."""
    result = compute_occurrence_streak(
        [date(2026, 7, 9), date(2026, 8, 27)],
        as_of=date(2026, 8, 17),
    )

    assert result["last_nc_date"] == "2026-07-09"
    assert result["current_days_without_nc"] == 39
    assert result["nc_count"] == 1


def test_streak_zero_when_last_occurrence_is_as_of() -> None:
    result = compute_occurrence_streak(
        [date(2026, 8, 17)],
        as_of=date(2026, 8, 17),
    )
    assert result["current_days_without_nc"] == 0
    assert result["last_nc_date"] == "2026-08-17"


def test_streak_only_future_dates_falls_back_to_zero_without_reference() -> None:
    result = compute_occurrence_streak(
        [date(2026, 8, 27)],
        as_of=date(2026, 8, 17),
    )
    assert result["current_days_without_nc"] == 0
    assert result["last_nc_date"] is None
    assert result["nc_count"] == 0
