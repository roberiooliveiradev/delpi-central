from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
    build_sales_order_otd_filters,
    build_sales_order_otd_late_days_stats_sql,
    build_sales_order_otd_line_detail_sql,
    build_sales_order_otd_line_detail_where,
    build_sales_order_otd_lines_count_sql,
    build_sales_order_otd_lines_list_sql,
    build_sales_order_otd_recurring_customers_sql,
    build_sales_order_otd_sql,
    build_sales_order_otd_upcoming_promises_sql,
    build_sales_order_otd_worst_delays_sql,
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


def test_list_and_line_detail_sql_expose_unit_from_c6_um() -> None:
    where_clause, _ = build_sales_order_otd_filters(
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
    )
    list_sql, _ = build_sales_order_otd_lines_list_sql(
        where_clause=where_clause,
        request=GetSalesOrderOtdPanelRequest(page=1, page_size=20),
        reference_end_date="2026-08-14",
    )
    detail_sql = build_sales_order_otd_line_detail_sql(where_clause=where_clause)
    worst_sql, _ = build_sales_order_otd_worst_delays_sql(
        where_clause=where_clause,
        reference_end_date="2026-08-14",
    )
    for sql in (list_sql, detail_sql, worst_sql):
        assert "C6.C6_UM" in sql
        assert "B1.B1_UM" in sql
        assert " AS unit" in sql


def test_analysis_sql_exposes_homogeneous_or_mixed_unit() -> None:
    from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_sql import (
        build_sales_order_otd_analysis_by_customer_sql,
        build_sales_order_otd_analysis_summary_sql,
    )

    where_clause, _ = build_sales_order_otd_filters(
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
    )
    summary_sql, _ = build_sales_order_otd_analysis_summary_sql(
        where_clause=where_clause,
        reference_end_date="2026-08-14",
    )
    by_customer_sql, _ = build_sales_order_otd_analysis_by_customer_sql(
        where_clause=where_clause,
        reference_end_date="2026-08-14",
    )
    for sql in (summary_sql, by_customer_sql):
        assert "C6.C6_UM" in sql
        assert "COUNT(DISTINCT unit)" in sql
        assert "mixed_units" in sql


def test_build_sales_order_otd_filters_treats_branch_all_as_consolidated() -> None:
    where_all, params_all = build_sales_order_otd_filters(
        branch="all",
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
    )
    where_none, params_none = build_sales_order_otd_filters(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
    )
    assert "C6.C6_FILIAL" not in where_all
    assert "all" not in where_all
    assert where_all == where_none
    assert params_all == params_none


def test_build_sales_order_otd_filters_keeps_concrete_branch() -> None:
    where_clause, params = build_sales_order_otd_filters(
        branch="01",
        start_date=None,
        end_date=None,
        customer_segment=None,
    )
    assert "C6.C6_FILIAL" in where_clause
    assert "01" in params


def test_build_sales_order_otd_filters_applies_customer_code_stores() -> None:
    where_clause, params = build_sales_order_otd_filters(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
        customer_codes=["000001"],
        customer_code_stores=[("000001", "01"), ("000001", "05")],
    )
    assert "C5.C5_CLIENTE IN" in where_clause
    assert "C5.C5_LOJACLI = ?" in where_clause
    assert "01" in params
    assert "05" in params
    assert params.count("000001") >= 3


def test_build_sales_order_otd_filters_without_pairs_omits_loja_predicate() -> None:
    where_clause, _ = build_sales_order_otd_filters(
        branch="02",
        start_date="2026-08-01",
        end_date="2026-08-14",
        customer_segment=None,
        customer_codes=["000001"],
    )
    assert "C5.C5_LOJACLI" not in where_clause


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
    assert "A1_NREDUZ" in sql
    assert "customer_short_name" in sql
    assert "COALESCE" in sql


def test_build_sales_order_otd_lines_list_supports_search() -> None:
    request = GetSalesOrderOtdPanelRequest(
        status="late",
        page=1,
        page_size=20,
        search="WEG",
    )
    sql, _ = build_sales_order_otd_lines_list_sql(
        where_clause="1=1",
        request=request,
        reference_end_date="2026-07-08",
    )
    assert "order_number LIKE ?" in sql
    assert "product_code LIKE ?" in sql
    assert "WHERE status = 'late'" in sql


def test_compose_sales_order_otd_lines_params_includes_search() -> None:
    params = compose_sales_order_otd_lines_params(
        where_params=("02",),
        reference_end_date="2026-07-08",
        search_params=("%WEG%",) * 6,
        offset=0,
        page_size=20,
    )
    assert params[:3] == ("20260708", "20260708", "20260708")
    assert params[3] == "02"
    assert params[4:10] == ("%WEG%",) * 6
    assert params[-2:] == (0, 20)


def test_build_sales_order_otd_insights_sql_shapes() -> None:
    stats_sql, _ = build_sales_order_otd_late_days_stats_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )
    recurring_sql, _ = build_sales_order_otd_recurring_customers_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )
    worst_sql, _ = build_sales_order_otd_worst_delays_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )
    upcoming_sql, _ = build_sales_order_otd_upcoming_promises_sql(
        where_clause="1=1",
        reference_end_date="2026-07-08",
    )
    assert "PERCENTILE_CONT(0.5)" in stats_sql
    assert "C5_LOJACLI" in recurring_sql
    assert "HAVING COUNT(*) >= 2" in recurring_sql
    assert "customer_store" in recurring_sql
    assert "GROUP BY customer_code, customer_store" in recurring_sql
    assert "WHERE status = 'late'" in worst_sql
    assert "is_invoiced = 0" in upcoming_sql
