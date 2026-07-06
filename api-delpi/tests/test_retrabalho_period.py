from datetime import date

from app.application.dto.retrabalho.retrabalho_period import RetrabalhoPeriod

def test_retrabalho_period_defaults_to_last_12_months() -> None:
    period = RetrabalhoPeriod.resolve(filial="01")
    assert period.filial == "01"
    assert period.end_date == date.today()
    assert period.start_date.day == 1
    months = (
        (period.end_date.year - period.start_date.year) * 12
        + (period.end_date.month - period.start_date.month)
        + 1
    )
    assert months == 12


def test_retrabalho_period_rejects_invalid_branch() -> None:
    try:
        RetrabalhoPeriod.resolve(filial="03")
    except ValueError as exc:
        assert "filial" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid branch")


def test_retrabalho_period_rejects_range_over_24_months() -> None:
    try:
        RetrabalhoPeriod.resolve(
            filial="01",
            data_inicio="2020-01-01",
            data_fim="2026-07-06",
        )
    except ValueError as exc:
        assert "24" in str(exc)
    else:
        raise AssertionError("expected ValueError for long range")
