from datetime import date

from app.application.dto.refugos.refugos_period import RefugosPeriod


def test_month_closed_open_is_full_calendar_month_of_data_fim() -> None:
    """valorMes não deve depender do dia de dataFim dentro do mês."""
    mid = RefugosPeriod(start_date=date(2026, 7, 13), end_date=date(2026, 7, 14), filial="01")
    end = RefugosPeriod(start_date=date(2026, 7, 13), end_date=date(2026, 7, 15), filial="01")
    december = RefugosPeriod(
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 10),
        filial="02",
    )

    assert mid.month_closed_open() == ("20260701", "20260801")
    assert end.month_closed_open() == ("20260701", "20260801")
    assert mid.month_closed_open() == end.month_closed_open()
    assert december.month_closed_open() == ("20251201", "20260101")


def test_day_closed_open_follows_data_fim() -> None:
    period = RefugosPeriod(start_date=date(2026, 7, 13), end_date=date(2026, 7, 14), filial="01")
    assert period.day_closed_open() == ("20260714", "20260715")
