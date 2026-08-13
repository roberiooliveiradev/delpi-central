from unittest.mock import MagicMock

from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.use_cases.commercial.get_sales_order_otd_series_use_case import (
    GetSalesOrderOtdSeriesUseCase,
)


def test_sales_order_otd_series_accepts_customer_codes_without_typeerror() -> None:
    repository = MagicMock()
    indicator = MagicMock()
    indicator.sales_order_otd_pct = 91.5
    repository.get_sales_order_otd.return_value = indicator

    use_case = GetSalesOrderOtdSeriesUseCase(sales_order_otd_repository=repository)
    result = use_case.execute(
        SalesOrderOtdSeriesRequest(
            granularity="month",
            date_start="2026-08-01",
            date_end="2026-08-13",
            branch="02",
            customer_codes=["000123", "000456"],
        )
    )

    assert result.points
    assert result.points[0].otd_filial_01 is None
    assert result.points[0].otd_filial_02 == 91.5

    calls = repository.get_sales_order_otd.call_args_list
    assert calls
    for call in calls:
        request = call.args[0]
        assert request.customer_codes == ["000123", "000456"]
        assert request.branch == "02"
