from datetime import date

from app.domain.services.kaizen import kaizen_savings_validity as validity


def test_valid_until_is_one_year_minus_one_day():
    implemented = date(2026, 1, 10)
    assert validity.savings_anniversary(implemented) == date(2027, 1, 10)
    assert validity.savings_valid_until(implemented) == date(2027, 1, 9)


def test_valid_until_handles_leap_day():
    implemented = date(2024, 2, 29)
    assert validity.savings_anniversary(implemented) == date(2025, 2, 28)


def test_none_implemented_is_never_active():
    assert validity.savings_valid_until(None) is None
    assert validity.is_savings_active(None) is False
    assert validity.active_days_in_range(None, None, None) == 0


def test_is_active_within_window():
    implemented = date(2026, 1, 10)
    assert validity.is_savings_active(
        implemented, status="implantado", reference=date(2026, 6, 1)
    )
    # Último dia válido.
    assert validity.is_savings_active(
        implemented, status="implantado", reference=date(2027, 1, 9)
    )


def test_is_inactive_after_one_year():
    implemented = date(2026, 1, 10)
    # No aniversário já não conta mais.
    assert not validity.is_savings_active(
        implemented, status="implantado", reference=date(2027, 1, 10)
    )
    assert not validity.is_savings_active(
        implemented, status="implantado", reference=date(2027, 6, 1)
    )


def test_is_inactive_when_not_implemented():
    implemented = date(2026, 1, 10)
    assert not validity.is_savings_active(
        implemented, status="em_andamento", reference=date(2026, 6, 1)
    )


def test_active_days_full_year_is_365():
    implemented = date(2026, 1, 10)
    days = validity.active_days_in_range(
        implemented, date(2026, 1, 10), date(2030, 1, 1)
    )
    assert days == 365


def test_active_days_zero_when_range_after_validity():
    implemented = date(2026, 1, 10)
    days = validity.active_days_in_range(
        implemented, date(2027, 2, 1), date(2027, 3, 1)
    )
    assert days == 0


def test_active_days_capped_partial_range():
    implemented = date(2026, 1, 10)
    # Intervalo cobre o fim da validade (09/01/2027) e além.
    days = validity.active_days_in_range(
        implemented, date(2027, 1, 1), date(2027, 1, 31)
    )
    # 01/01/2027 .. 09/01/2027 = 9 dias.
    assert days == 9
