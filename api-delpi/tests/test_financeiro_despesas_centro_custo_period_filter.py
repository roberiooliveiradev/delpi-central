from app.application.dto.financeiro_despesas_centro_custo.period_filter_request import (
    PeriodFilterRequest,
)


def test_period_filter_request_normalizes_iso_dates_to_protheus() -> None:
    request = PeriodFilterRequest.from_query(
        start_date="2025-06-01",
        end_date="20250630",
    )

    start, end = request.resolve_protheus_period()
    assert start == "20250601"
    assert end == "20250630"


def test_period_filter_request_rejects_inverted_range() -> None:
    request = PeriodFilterRequest.from_query(
        start_date="2025-07-01",
        end_date="2025-06-01",
    )

    try:
        request.resolve_protheus_period()
    except ValueError as exc:
        assert "start_date" in str(exc)
    else:
        raise AssertionError("expected ValueError for inverted date range")
