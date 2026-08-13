from unittest.mock import MagicMock, patch

from app.application.dto.commercial.sales_conversion_rate_series_request import (
    SalesConversionRateSeriesRequest,
)
from app.application.use_cases.commercial.get_sales_conversion_rate_series_use_case import (
    GetSalesConversionRateSeriesUseCase,
)
from app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate


def test_sales_conversion_rate_series_returns_points_per_bucket() -> None:
    repository = MagicMock()

    def fake_rate(request):
        if request.branch == "01":
            return SalesConversionRate(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                qtd_proposals=20,
                qtd_won=5,
                sales_conversion_rate_pct=25.0,
            )
        return SalesConversionRate(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            qtd_proposals=10,
            qtd_won=1,
            sales_conversion_rate_pct=10.0,
        )

    repository.get_sales_conversion_rate.side_effect = fake_rate

    use_case = GetSalesConversionRateSeriesUseCase(
        sales_conversion_rate_repository=repository
    )

    with patch(
        "app.application.use_cases.commercial.get_sales_conversion_rate_series_use_case.get_cached_chart_series",
        return_value=None,
    ), patch(
        "app.application.use_cases.commercial.get_sales_conversion_rate_series_use_case.set_cached_chart_series",
    ):
        result = use_case.execute(
            SalesConversionRateSeriesRequest(
                granularity="month",
                date_start="2026-01-01",
                date_end="2026-02-28",
            )
        )

    assert result.granularity == "month"
    assert result.truncated is False
    assert len(result.points) == 2
    first = result.points[0]
    assert first.conversion_filial_01 == 25.0
    assert first.conversion_filial_02 == 10.0
    assert first.qtd_proposals_01 == 20
    assert first.qtd_won_02 == 1
    assert repository.get_sales_conversion_rate.call_count == 4


def test_sales_conversion_rate_series_rejects_invalid_granularity() -> None:
    use_case = GetSalesConversionRateSeriesUseCase(
        sales_conversion_rate_repository=MagicMock()
    )
    try:
        use_case.execute(SalesConversionRateSeriesRequest(granularity="hour"))
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "granularity" in str(exc).lower()
