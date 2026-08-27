from unittest.mock import MagicMock, patch

from app.application.dto.commercial.get_sales_order_otd_series_by_customer_request import (
    GetSalesOrderOtdSeriesByCustomerRequest,
)
from app.application.use_cases.commercial.get_sales_order_otd_series_by_customer_use_case import (
    GetSalesOrderOtdSeriesByCustomerUseCase,
)


def _customer_row(
    *,
    code: str,
    name: str,
    total_qty: float,
    otd_pct: float,
    store: str = "01",
    branch: str = "01",
) -> dict:
    return {
        "customer_code": code,
        "customer_store": store,
        "customer_name": name,
        "branch": branch,
        "total_lines": 2,
        "total_qty": total_qty,
        "fulfilled_qty": total_qty * 0.8,
        "on_time_lines": 1,
        "late_lines": 1,
        "fulfillment_pct": 80.0,
        "otd_pct": otd_pct,
    }


_CACHE_GET = (
    "app.application.use_cases.commercial."
    "get_sales_order_otd_series_by_customer_use_case.get_cached_chart_series"
)
_CACHE_SET = (
    "app.application.use_cases.commercial."
    "get_sales_order_otd_series_by_customer_use_case.set_cached_chart_series"
)


@patch(_CACHE_SET)
@patch(_CACHE_GET, return_value=None)
def test_series_by_customer_emits_customer_times_bucket_rows(
    _mock_get, _mock_set
) -> None:
    repository = MagicMock()

    def _list(request):
        if request.customer_codes:
            return [
                _customer_row(code="A", name="Alpha", total_qty=10.0, otd_pct=50.0),
                _customer_row(code="B", name="Beta", total_qty=5.0, otd_pct=80.0),
            ]
        return [
            _customer_row(code="A", name="Alpha", total_qty=100.0, otd_pct=60.0),
            _customer_row(code="B", name="Beta", total_qty=50.0, otd_pct=70.0),
            _customer_row(code="C", name="Gamma", total_qty=10.0, otd_pct=90.0),
        ]

    repository.list_sales_order_otd_analysis_by_customer.side_effect = _list
    use_case = GetSalesOrderOtdSeriesByCustomerUseCase(
        sales_order_otd_repository=repository
    )
    result = use_case.execute(
        GetSalesOrderOtdSeriesByCustomerRequest(
            granularity="week",
            date_start="2026-08-03",
            date_end="2026-08-16",
            top_customers=2,
            page=1,
            page_size=50,
        )
    )

    assert result["granularity"] == "week"
    assert result["summary"]["customers_count"] == 2
    assert result["summary"]["buckets_count"] == 2
    assert len(result["items"]) == 4
    assert result["items"][0]["periodo"]
    assert result["items"][0]["customer_name"]
    assert result["items"][0]["otd_pct"] is not None
    assert all(item["customer_code"] in {"A", "B"} for item in result["items"])


@patch(_CACHE_SET)
@patch(_CACHE_GET, return_value=None)
def test_series_by_customer_respects_customer_names_without_top(
    _mock_get, _mock_set
) -> None:
    repository = MagicMock()
    repository.list_sales_order_otd_analysis_by_customer.return_value = [
        _customer_row(code="W", name="WEG Amazonia", total_qty=20.0, otd_pct=95.0),
    ]
    use_case = GetSalesOrderOtdSeriesByCustomerUseCase(
        sales_order_otd_repository=repository
    )
    result = use_case.execute(
        GetSalesOrderOtdSeriesByCustomerRequest(
            granularity="week",
            date_start="2026-08-03",
            date_end="2026-08-09",
            customer_names=["WEG Amazonia"],
        )
    )
    assert len(result["items"]) == 1
    assert result["items"][0]["customer_name"] == "WEG Amazonia"
    for call in repository.list_sales_order_otd_analysis_by_customer.call_args_list:
        req = call.args[0]
        assert req.customer_names == ["WEG Amazonia"]


@patch(_CACHE_SET)
@patch(_CACHE_GET, return_value=None)
def test_series_by_customer_defaults_granularity_to_week(
    _mock_get, _mock_set
) -> None:
    repository = MagicMock()
    repository.list_sales_order_otd_analysis_by_customer.return_value = [
        _customer_row(code="A", name="Alpha", total_qty=10.0, otd_pct=50.0),
    ]
    use_case = GetSalesOrderOtdSeriesByCustomerUseCase(
        sales_order_otd_repository=repository
    )
    result = use_case.execute(
        GetSalesOrderOtdSeriesByCustomerRequest(
            date_start="2026-08-03",
            date_end="2026-08-09",
            customer_codes=["A"],
        )
    )
    assert result["granularity"] == "week"
    assert result["items"]


@patch(_CACHE_SET)
@patch(_CACHE_GET, return_value=None)
def test_series_by_customer_paginates_flat_items(_mock_get, _mock_set) -> None:
    repository = MagicMock()
    repository.list_sales_order_otd_analysis_by_customer.return_value = [
        _customer_row(code="A", name="Alpha", total_qty=10.0, otd_pct=50.0),
        _customer_row(code="B", name="Beta", total_qty=5.0, otd_pct=80.0),
    ]
    use_case = GetSalesOrderOtdSeriesByCustomerUseCase(
        sales_order_otd_repository=repository
    )
    result = use_case.execute(
        GetSalesOrderOtdSeriesByCustomerRequest(
            granularity="week",
            date_start="2026-08-03",
            date_end="2026-08-16",
            customer_codes=["A", "B"],
            page=1,
            page_size=2,
        )
    )
    assert result["pagination"]["total"] == 4
    assert result["pagination"]["has_more"] is True
    assert len(result["items"]) == 2
