from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_filters,
    build_sales_order_otd_line_detail_sql,
    build_sales_order_otd_line_detail_where,
    build_sales_order_otd_lines_count_sql,
    build_sales_order_otd_lines_list_sql,
    build_sales_order_otd_sql,
    compose_sales_order_otd_lines_params,
    _list_order_clause,
)


def test_build_sales_order_otd_filters_includes_open_lines_without_invoice_requirement() -> None:
    where_clause, _ = build_sales_order_otd_filters(
        branch="02",
        start_date="2026-07-01",
        end_date="2026-07-08",
        customer_segment="weg",
    )

    assert "C6.C6_DATFAT IS NOT NULL" not in where_clause
    assert "C6.C6_QTDENT >= C6.C6_QTDVEN" not in where_clause
    assert "C6.C6_QTDVEN > 0" in where_clause
    assert "C6.C6_ENTREG" in where_clause


def test_build_sales_order_otd_sql_classifies_invoiced_and_open_lines() -> None:
    sql, params = build_sales_order_otd_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )

    assert "linhas_elegiveis" in sql
    assert "C6_DATFAT <= C6_ENTREG" in sql
    assert "COALESCE(?, CONVERT(VARCHAR(8), GETDATE(), 112)) > C6_ENTREG" in sql
    assert params == ("20260708", "20260708", "20260708")


def test_build_sales_order_otd_lines_count_supports_status_filter() -> None:
    sql, _ = build_sales_order_otd_lines_count_sql(
        where_clause="1=1",
        status="late",
        reference_end_date="2026-07-08",
    )

    assert "LINHAS_ELEGIVEIS" in sql
    assert "WHERE status = 'late'" in sql


def test_compose_sales_order_otd_lines_params_reference_before_where() -> None:
    params = compose_sales_order_otd_lines_params(
        where_params=("02", "20260701", "20260708"),
        reference_end_date="2026-07-08",
        offset=0,
        page_size=20,
    )

    assert params == ("20260708", "20260708", "20260708", "02", "20260701", "20260708", 0, 20)


def test_build_sales_order_otd_line_detail_where_applies_period_and_identity() -> None:
    where_clause, where_params = build_sales_order_otd_line_detail_where(
        branch="01",
        order_number="102767",
        line_item="06",
        start_date="2026-07-01",
        end_date="2026-07-09",
        customer_segment=None,
    )

    assert "C6.C6_FILIAL = ?" in where_clause
    assert "C6.C6_ENTREG" in where_clause
    assert "LTRIM(RTRIM(C6.C6_NUM))" in where_clause
    assert "LTRIM(RTRIM(C6.C6_ITEM))" in where_clause
    assert where_params[-2:] == ("102767", "06")


def test_list_order_clause_avoids_duplicate_sort_column() -> None:
    request = GetSalesOrderOtdPanelRequest(
        branch=None,
        start_date="20260701",
        end_date="20260709",
        customer_segment=None,
        status=None,
        page=1,
        page_size=20,
        sort_by="line_item",
        sort_dir="asc",
    )

    order_clause = _list_order_clause(request)

    assert order_clause.count("line_item") == 1


def test_build_sales_order_otd_line_detail_sql_uses_shared_cte() -> None:
    sql = build_sales_order_otd_line_detail_sql(where_clause="1=1")

    assert "LINHAS_ELEGIVEIS" in sql
    assert "SELECT TOP 1 *" in sql
