from datetime import date

from tm_app.core.brazil_national_holidays import easter_sunday, is_national_holiday
from tm_app.core.business_days import USE_ONLY_BUSINESS_DAYS, business_days_in_month, is_business_day


def test_easter_sunday_2026():
    assert easter_sunday(2026) == date(2026, 4, 5)


def test_corpus_christi_2026_is_national_holiday():
    assert is_national_holiday(date(2026, 6, 4)) is True


def test_corpus_christi_counts_when_business_days_disabled():
    assert USE_ONLY_BUSINESS_DAYS is False
    assert is_business_day(date(2026, 6, 4)) is True
    assert business_days_in_month(2026, 6) == 30
