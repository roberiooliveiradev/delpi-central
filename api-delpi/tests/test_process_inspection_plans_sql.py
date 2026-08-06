"""SQL builders — process inspection plans."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.process_inspection_plans import (
    process_inspection_plans_sql as sql,
)


def test_summary_sql_includes_core_tables_and_open_predicate() -> None:
    query, params = sql.build_summary_sql("01")
    assert "SC2010" in query
    assert "QP6010" in query
    assert "C2_DATRF" in query
    assert "NOLOCK" in query
    assert "OP.C2_FILIAL = ?" in query
    assert params == ("01",)


def test_summary_sql_all_branches_skips_filial_predicate() -> None:
    query, params = sql.build_summary_sql("all")
    assert "OP.C2_FILIAL = ?" not in query
    assert params == ()


def test_orders_without_plan_sql_uses_offset_fetch() -> None:
    query, params = sql.build_list_orders_without_plan_sql(
        "01", offset=0, page_size=50
    )
    assert "C2_YOBSQUA" in query
    assert "SB1010" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params[-2:] == (0, 50)


def test_products_with_plan_sql_uses_max_revision() -> None:
    query, params = sql.build_list_products_with_plan_sql(offset=0, page_size=20)
    assert "MAX(QP6_REVI)" in query
    assert "QP6010" in query
    assert params == (0, 20)


def test_product_has_plan_sql() -> None:
    query, params = sql.build_product_has_plan_sql("80010001")
    assert "QP6010" in query
    assert params == ("80010001",)
