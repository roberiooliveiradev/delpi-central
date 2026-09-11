from datetime import date

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    build_purchase_orders_list_count_sql,
    build_purchase_orders_list_filters,
    build_purchase_orders_list_sql,
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
