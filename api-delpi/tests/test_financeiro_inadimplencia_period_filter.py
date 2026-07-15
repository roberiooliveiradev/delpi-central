from datetime import date

from app.application.dto.financeiro_inadimplencia.constantes import (
    MAX_PERIOD_MONTHS,
    PERIODO_PADRAO_ROTULO,
)
from app.application.dto.financeiro_inadimplencia.period_filter_request import (
    PeriodFilterRequest,
    resolve_default_period,
)


def test_default_period_uses_last_12_complete_months() -> None:
    start, end_exclusive = resolve_default_period(today=date(2026, 7, 14))
    assert start == date(2025, 7, 1)
    assert end_exclusive == date(2026, 7, 1)


def test_period_filter_default_when_dates_omitted() -> None:
    request = PeriodFilterRequest.from_query()
    start, end_exclusive, rotulo = request.resolve_period(today=date(2026, 7, 14))
    assert start == date(2025, 7, 1)
    assert end_exclusive == date(2026, 7, 1)
    assert rotulo == PERIODO_PADRAO_ROTULO


def test_period_filter_custom_range() -> None:
    request = PeriodFilterRequest.from_query(
        start_date="2025-01-01",
        end_date="2025-07-01",
    )
    start, end_exclusive, rotulo = request.resolve_period()
    assert start == date(2025, 1, 1)
    assert end_exclusive == date(2025, 7, 1)
    assert "personalizado" in rotulo.lower()


def test_period_filter_rejects_partial_range() -> None:
    try:
        PeriodFilterRequest.from_query(start_date="2025-01-01")
    except ValueError as exc:
        assert "juntos" in str(exc)
    else:
        raise AssertionError("expected ValueError for partial period")


def test_period_filter_rejects_inverted_or_equal_range() -> None:
    request = PeriodFilterRequest.from_query(
        start_date="2025-07-01",
        end_date="2025-07-01",
    )
    try:
        request.resolve_period()
    except ValueError as exc:
        assert "anterior" in str(exc)
    else:
        raise AssertionError("expected ValueError for equal range")


def test_period_filter_rejects_range_above_maximum() -> None:
    request = PeriodFilterRequest.from_query(
        start_date="2020-01-01",
        end_date="2026-01-01",
    )
    try:
        request.resolve_period()
    except ValueError as exc:
        assert str(MAX_PERIOD_MONTHS) in str(exc)
    else:
        raise AssertionError("expected ValueError for excessive range")
