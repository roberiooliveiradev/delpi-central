from datetime import date

from tm_app.core.business_days import (
    USE_ONLY_BUSINESS_DAYS,
    business_day_fraction_in_competencia_range,
    business_days_in_month,
    business_days_overlap_in_competencia,
    count_business_days,
    is_business_day,
)


def test_business_days_mode_disabled():
    assert USE_ONLY_BUSINESS_DAYS is False


def test_weekend_counts_as_day_when_disabled():
    assert is_business_day(date(2026, 6, 6)) is True  # Saturday


def test_june_2026_calendar_days_in_month():
    assert business_days_in_month(2026, 6) == 30


def test_june_2026_partial_filter_fraction():
    fraction = business_day_fraction_in_competencia_range(
        "2026-06",
        "2026-06-01",
        "2026-06-03",
        uses_day_level_filter=True,
    )
    assert abs(fraction - (3 / 30)) < 1e-6


def test_overlap_counts_all_days_in_range():
    overlap = business_days_overlap_in_competencia(
        "2026-06",
        date(2026, 6, 1),
        date(2026, 6, 7),
    )
    assert overlap == count_business_days(date(2026, 6, 1), date(2026, 6, 7))
