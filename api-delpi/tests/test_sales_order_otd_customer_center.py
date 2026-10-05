"""Commercial sales-order OTD — authoritative ``customer_center`` (SA7.A7_XCENT).

Covers the contract correction: the center must be resolved by the canonical
SA7 grouped link in every grain that supports it — even when the
``customer_centers`` request filter is absent — and must never be echoed from
the request or fabricated on multi-center aggregates.
"""

from __future__ import annotations

from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_analysis_by_customer_sql,
    build_sales_order_otd_analysis_summary_sql,
    build_sales_order_otd_filters,
    build_sales_order_otd_line_detail_sql,
    build_sales_order_otd_lines_list_sql,
    build_sales_order_otd_sql,
    build_sales_order_otd_upcoming_promises_sql,
    build_sales_order_otd_worst_delays_sql,
    sales_order_otd_center_resolution_join,
)


class _StubbedRepository(SalesOrderOtdRepository):
    """Captures generated SQL and replays canned rows; no DB connection."""

    def __init__(self, rows: list[dict]) -> None:
        super().__init__()
        self._rows = rows
        self.captured_sql: list[str] = []
        self.captured_params: list[tuple] = []

    def _connect(self):
        return None

    def _close(self, *, discard: bool = False):
        return None

    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        self.captured_sql.append(query)
        self.captured_params.append(params)
        return [dict(row) for row in self._rows]


def _by_customer_row(customer_center) -> dict:
    return {
        "customer_code": "000001",
        "customer_store": "06",
        "customer_name": "WEG AMAZONIA",
        "customer_center": customer_center,
        "branch": "01",
        "total_lines": 3,
        "total_qty": 12.0,
        "fulfilled_qty": 9.0,
        "on_time_lines": 2,
        "late_lines": 1,
        "fulfillment_pct": 75.0,
        "otd_pct": 66.67,
        "unit": "PC",
        "mixed_units": 0,
    }


def test_resolution_join_left_joins_sa7_without_filter() -> None:
    join = sales_order_otd_center_resolution_join(None)

    assert "LEFT JOIN" in join
    assert "INNER JOIN" not in join
    assert "SA7010" in join
    assert "A7_XCENT" in join
    # Grouped link is 1:1 per product+customer+store: never multiplies lines.
    assert "GROUP BY" in join


def test_resolution_join_empty_list_still_resolves_column() -> None:
    # ``[]`` means "explicitly filtered to nothing" (1=0 in WHERE); the
    # LEFT join only makes the projection resolvable — harmless on empty sets.
    join = sales_order_otd_center_resolution_join([])

    assert "LEFT JOIN" in join
    assert "SA7010" in join


def test_resolution_join_keeps_inner_filter_when_centers_given() -> None:
    join = sales_order_otd_center_resolution_join(["1700"])

    assert "INNER JOIN" in join
    assert "LEFT JOIN" not in join
    assert "SA7010" in join


def test_by_customer_sql_resolves_center_without_center_filter() -> None:
    where_clause, _ = build_sales_order_otd_filters(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_segment=None,
    )
    sql, _ = build_sales_order_otd_analysis_by_customer_sql(
        where_clause=where_clause,
        center_join=sales_order_otd_center_resolution_join(None),
    )

    assert "LEFT JOIN" in sql
    assert "SA7010" in sql
    assert "SA7C.customer_center" in sql
    # Multi-center customer+store groups must stay unclassified (NULL), never
    # collapsed into an arbitrary single center.
    assert "COUNT(DISTINCT customer_center) = 1" in sql
    assert "CAST(NULL AS VARCHAR(20))" not in sql
    # Grain is unchanged: customer + store, not customer + store + center.
    assert "GROUP BY customer_code, customer_store" in sql


def test_by_customer_sql_preserves_center_filter_and_formulas() -> None:
    where_clause, params = build_sales_order_otd_filters(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_segment=None,
        customer_centers=["1106", "1320"],
    )
    sql, _ = build_sales_order_otd_analysis_by_customer_sql(
        where_clause=where_clause,
        center_join=sales_order_otd_center_resolution_join(["1106", "1320"]),
    )

    assert "SA7C.customer_center IN" in where_clause
    assert "INNER JOIN" in sql
    assert params.count("1106") == 1
    assert params.count("1320") == 1
    # OTD/fulfillment formulas untouched by the center projection.
    assert "SUM(is_on_time) * 100.0 / COUNT(*)" in sql
    assert "SUM(qty_delivered) * 100.0 / SUM(qty_sold)" in sql


def test_line_grain_sql_resolves_center_without_filter() -> None:
    join = sales_order_otd_center_resolution_join(None)
    request = GetSalesOrderOtdPanelRequest(page=1, page_size=20)
    list_sql, _ = build_sales_order_otd_lines_list_sql(
        where_clause="1=1", request=request, center_join=join
    )
    detail_sql = build_sales_order_otd_line_detail_sql(
        where_clause="1=1", center_join=join
    )
    worst_sql, _ = build_sales_order_otd_worst_delays_sql(
        where_clause="1=1", center_join=join
    )
    upcoming_sql, _ = build_sales_order_otd_upcoming_promises_sql(
        where_clause="1=1", center_join=join
    )

    for sql in (list_sql, detail_sql, worst_sql, upcoming_sql):
        assert "SA7C.customer_center" in sql
        assert "LEFT JOIN" in sql
        assert "CAST(NULL AS VARCHAR(20))" not in sql


def test_scalar_and_summary_queries_keep_sa7_out_without_filter() -> None:
    # Aggregate-only surfaces must not pay the center join for a column they
    # never project.
    scalar_sql, _ = build_sales_order_otd_sql(where_clause="1=1")
    summary_sql, _ = build_sales_order_otd_analysis_summary_sql(
        where_clause="1=1"
    )
    assert "SA7010" not in scalar_sql
    assert "SA7010" not in summary_sql


def test_by_customer_returns_center_from_row_not_request() -> None:
    repo = _StubbedRepository([_by_customer_row("1700")])

    rows = repo.list_sales_order_otd_analysis_by_customer(
        SalesOrderOtdRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            customer_centers=["1700"],
        )
    )

    assert rows[0]["customer_center"] == "1700"
    # The INNER filter join is still the filter path when centers are given.
    assert "INNER JOIN" in repo.captured_sql[0]


def test_by_customer_never_echoes_request_centers() -> None:
    """The response value comes from the SA7 row, never from the filter."""
    repo = _StubbedRepository([_by_customer_row("9999")])

    rows = repo.list_sales_order_otd_analysis_by_customer(
        SalesOrderOtdRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            customer_centers=["1700"],
        )
    )

    assert rows[0]["customer_center"] == "9999"


def test_by_customer_unfiltered_query_resolves_center_via_left_sa7() -> None:
    repo = _StubbedRepository([_by_customer_row("1106")])

    rows = repo.list_sales_order_otd_analysis_by_customer(
        SalesOrderOtdRequest(start_date="2026-08-01", end_date="2026-08-31")
    )

    sql = repo.captured_sql[0]
    assert "LEFT JOIN" in sql
    assert "SA7010" in sql
    assert "SA7C.customer_center" in sql
    assert rows[0]["customer_center"] == "1106"


def test_by_customer_ambiguous_center_stays_null_and_metrics_hold() -> None:
    repo = _StubbedRepository([_by_customer_row(None)])

    rows = repo.list_sales_order_otd_analysis_by_customer(
        SalesOrderOtdRequest(start_date="2026-08-01", end_date="2026-08-31")
    )

    row = rows[0]
    assert row["customer_center"] is None
    assert row["otd_pct"] == 66.67
    assert row["fulfillment_pct"] == 75.0
    assert row["total_lines"] == 3
    assert row["on_time_lines"] == 2
    assert row["late_lines"] == 1


def test_by_customer_center_value_is_trimmed() -> None:
    repo = _StubbedRepository([_by_customer_row("  1320  ")])

    rows = repo.list_sales_order_otd_analysis_by_customer(
        SalesOrderOtdRequest(start_date="2026-08-01", end_date="2026-08-31")
    )

    assert rows[0]["customer_center"] == "1320"
