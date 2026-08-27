from unittest.mock import MagicMock

from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.use_cases.commercial.get_sales_order_otd_series_use_case import (
    GetSalesOrderOtdSeriesUseCase,
)


def _summary(
    *,
    total_qty: float,
    fulfilled_qty: float,
    total_lines: int,
    on_time_lines: int,
    otd_pct: float,
    fulfillment_pct: float,
) -> dict:
    return {
        "total_qty": total_qty,
        "fulfilled_qty": fulfilled_qty,
        "total_lines": total_lines,
        "on_time_lines": on_time_lines,
        "late_lines": max(total_lines - on_time_lines, 0),
        "otd_pct": otd_pct,
        "fulfillment_pct": fulfillment_pct,
    }


def test_sales_order_otd_series_accepts_customer_codes_without_typeerror() -> None:
    repository = MagicMock()
    repository.get_sales_order_otd_analysis_summary.return_value = _summary(
        total_qty=10.0,
        fulfilled_qty=8.0,
        total_lines=4,
        on_time_lines=3,
        otd_pct=91.5,
        fulfillment_pct=80.0,
    )

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
    assert result.points[0].total_qty == 10.0
    assert result.points[0].fulfilled_qty == 8.0
    assert result.points[0].otd_pct == 91.5

    calls = repository.get_sales_order_otd_analysis_summary.call_args_list
    assert calls
    for call in calls:
        request = call.args[0]
        assert request.customer_codes == ["000123", "000456"]
        assert request.branch == "02"


def test_sales_order_otd_series_consolidates_qty_and_otd_with_customer_names() -> None:
    repository = MagicMock()

    def _side_effect(request):
        if request.branch == "01":
            return _summary(
                total_qty=100.0,
                fulfilled_qty=90.0,
                total_lines=10,
                on_time_lines=8,
                otd_pct=80.0,
                fulfillment_pct=90.0,
            )
        return _summary(
            total_qty=50.0,
            fulfilled_qty=40.0,
            total_lines=5,
            on_time_lines=4,
            otd_pct=80.0,
            fulfillment_pct=80.0,
        )

    repository.get_sales_order_otd_analysis_summary.side_effect = _side_effect
    use_case = GetSalesOrderOtdSeriesUseCase(sales_order_otd_repository=repository)
    result = use_case.execute(
        SalesOrderOtdSeriesRequest(
            granularity="week",
            date_start="2026-08-01",
            date_end="2026-08-07",
            customer_names=["WEG Amazonia"],
        )
    )

    point = result.points[0]
    assert point.otd_filial_01 == 80.0
    assert point.otd_filial_02 == 80.0
    assert point.total_qty == 150.0
    assert point.fulfilled_qty == 130.0
    assert point.total_lines == 15
    assert point.fulfillment_pct == round(130.0 * 100.0 / 150.0, 2)
    assert point.otd_pct == round(12 * 100.0 / 15, 2)

    for call in repository.get_sales_order_otd_analysis_summary.call_args_list:
        assert call.args[0].customer_names == ["WEG Amazonia"]


def test_sales_order_otd_series_branch_all_fetches_both_branches() -> None:
    repository = MagicMock()
    repository.get_sales_order_otd_analysis_summary.return_value = _summary(
        total_qty=10.0,
        fulfilled_qty=8.0,
        total_lines=4,
        on_time_lines=3,
        otd_pct=75.0,
        fulfillment_pct=80.0,
    )
    use_case = GetSalesOrderOtdSeriesUseCase(sales_order_otd_repository=repository)
    result = use_case.execute(
        SalesOrderOtdSeriesRequest(
            granularity="week",
            date_start="2026-08-03",
            date_end="2026-08-09",
            branch="all",
        )
    )
    assert result.branch is None
    assert result.points
    assert result.points[0].otd_pct is not None
    assert result.points[0].total_qty == 20.0  # 01+02
    branches = {call.args[0].branch for call in repository.get_sales_order_otd_analysis_summary.call_args_list}
    assert branches == {"01", "02"}
