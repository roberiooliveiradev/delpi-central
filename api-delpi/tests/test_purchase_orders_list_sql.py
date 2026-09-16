from datetime import date

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    _OPEN_VALUE_EXPRESSION,
    build_purchase_orders_list_count_sql,
    build_purchase_orders_list_filters,
    build_purchase_orders_list_sql,
    build_purchase_orders_summary_sql,
)


def test_filters_include_open_sc7_rules_and_branch() -> None:
    where_clause, params = build_purchase_orders_list_filters(branch="02")
    assert "SC7.D_E_L_E_T_ = ''" in where_clause
    assert "C7_RESIDUO" in where_clause
    assert "C7_QUANT > SC7.C7_QUJE" in where_clause
    assert "C7_FILIAL" in where_clause
    assert "02" in params


def test_order_number_filter_positive() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="01",
        order_number="041446",
    )
    assert "RTRIM(SC7.C7_NUM) = ?" in where_clause
    assert "041446" in params


def test_late_only_filter_sibling() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="01",
        late_only=True,
        reference=date(2026, 9, 11),
    )
    assert "C7_DATPRF" in where_clause
    assert "<> ''" in where_clause
    assert "20260911" in params
    assert params[-1] == "20260911"


def test_late_only_false_does_not_add_datprf_today_predicate() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="01",
        late_only=False,
        reference=date(2026, 9, 11),
    )
    assert "20260911" not in params
    assert "RTRIM(SC7.C7_DATPRF) < ?" not in where_clause


def test_count_and_list_sql_use_sc7010_and_offset() -> None:
    where_clause, _ = build_purchase_orders_list_filters(branch="01")
    count_sql = build_purchase_orders_list_count_sql(where_clause)
    list_sql = build_purchase_orders_list_sql(where_clause=where_clause)
    assert "SC7010" in count_sql
    assert "SC7010" in list_sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in list_sql
    assert "open_value" in list_sql
    assert "balance_factor" in list_sql
    assert _OPEN_VALUE_EXPRESSION in list_sql


def test_summary_sql_aggregates_without_pagination() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="01",
        order_number="000123",
        product_code="ABC",
        supplier_code="F001",
        expected_delivery_from="2026-01-01",
        expected_delivery_to="2026-12-31",
        late_only=False,
    )
    summary_sql = build_purchase_orders_summary_sql(where_clause=where_clause)
    assert "OFFSET" not in summary_sql
    assert "FETCH" not in summary_sql
    assert "total_lines" in summary_sql
    assert "total_open_value" in summary_sql
    assert "late_lines" in summary_sql
    assert "on_time_lines" in summary_sql
    assert "no_date_lines" in summary_sql
    assert "SC7010" in summary_sql
    assert "balance_factor" in summary_sql
    assert _OPEN_VALUE_EXPRESSION in summary_sql
    assert "C7_VALIPI" in summary_sql and "C7_VALFRE" in summary_sql
    assert "C7_VLDESC" in summary_sql
    assert where_clause in summary_sql
    assert "000123" in params
    assert "ABC" in params
    assert "F001" in params
    assert "20260101" in params
    assert "20261231" in params


def test_summary_filters_ignore_late_only_when_built_false() -> None:
    list_where, list_params = build_purchase_orders_list_filters(
        branch="01",
        product_code="ABC",
        late_only=True,
        reference=date(2026, 9, 11),
    )
    summary_where, summary_params = build_purchase_orders_list_filters(
        branch="01",
        product_code="ABC",
        late_only=False,
        reference=date(2026, 9, 11),
    )
    assert "RTRIM(SC7.C7_DATPRF) < ?" in list_where
    assert "20260911" in list_params
    assert "RTRIM(SC7.C7_DATPRF) < ?" not in summary_where
    assert "20260911" not in summary_params
    assert "ABC" in summary_params
    assert "SC7.D_E_L_E_T_ = ''" in summary_where
    assert "C7_QUANT > SC7.C7_QUJE" in summary_where


def test_summary_buckets_use_same_date_reference_semantics() -> None:
    where_clause, _ = build_purchase_orders_list_filters(branch="01")
    summary_sql = build_purchase_orders_summary_sql(where_clause=where_clause)
    assert summary_sql.count("RTRIM(SC7.C7_DATPRF) < ?") == 1
    assert summary_sql.count("RTRIM(SC7.C7_DATPRF) >= ?") == 1
    assert "RTRIM(ISNULL(SC7.C7_DATPRF, '')) = ''" in summary_sql
    assert "RTRIM(ISNULL(SC7.C7_DATPRF, '')) <> ''" in summary_sql


def test_list_and_summary_share_identical_open_value_expression() -> None:
    where_clause, _ = build_purchase_orders_list_filters(branch="01")
    list_sql = build_purchase_orders_list_sql(where_clause=where_clause)
    summary_sql = build_purchase_orders_summary_sql(where_clause=where_clause)
    assert _OPEN_VALUE_EXPRESSION in list_sql
    assert _OPEN_VALUE_EXPRESSION in summary_sql
    assert list_sql.count(_OPEN_VALUE_EXPRESSION) == 1
    assert summary_sql.count(_OPEN_VALUE_EXPRESSION) == 1
