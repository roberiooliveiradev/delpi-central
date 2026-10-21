"""SQL builders: snapshot filters, logical delete, SB1 join, aggregation."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.financeiro_stock_inventory import (
    stock_inventory_sql,
)


def test_items_query_snapshot_and_deletes():
    query, params = stock_inventory_sql.build_items_query(
        snapshot_date="20260930",
        branches=("01", "02"),
        product_types=None,
        warehouse=None,
        page=2,
        page_size=50,
    )
    assert "SB9010 S WITH (NOLOCK)" in query
    assert "S.B9_DATA = ?" in query
    assert "S.D_E_L_E_T_ = ''" in query
    assert "P.D_E_L_E_T_ = ''" in query
    assert "SB1010 P" in query
    assert "P.B1_COD = S.B9_COD" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert params == ["20260930", "01", "02", 50, 50]


def test_items_query_mp_pi_pa_and_warehouse():
    query, params = stock_inventory_sql.build_items_query(
        snapshot_date="20260930",
        branches=("01",),
        product_types=("MP", "PI", "PA"),
        warehouse="03",
        page=1,
        page_size=200,
    )
    assert "P.B1_TIPO IN (?, ?, ?)" in query
    assert "RTRIM(S.B9_LOCAL) = ?" in query
    assert params == ["20260930", "01", "MP", "PI", "PA", "03", 0, 200]


def test_grouped_grain_prevents_join_fanout():
    query, _ = stock_inventory_sql.build_items_query(
        snapshot_date="20260930",
        branches=("01",),
        product_types=None,
        warehouse=None,
        page=1,
        page_size=50,
    )
    assert "GROUP BY S.B9_FILIAL, S.B9_LOCAL, S.B9_COD" in query
    assert "SUM(S.B9_QINI)" in query
    assert "SUM(S.B9_VINI1)" in query


def test_branch_counts_unfiltered():
    query, params = stock_inventory_sql.build_snapshot_branch_counts_query(
        snapshot_date="20260930", branches=("01", "02")
    )
    assert "GROUP BY S.B9_FILIAL" in query
    assert "B1_TIPO" not in query  # no functional filter on presence check
    assert params == ["20260930", "01", "02"]


def test_totals_and_summaries_cover_full_universe():
    totals, params = stock_inventory_sql.build_totals_query(
        snapshot_date="20260930",
        branches=("02",),
        product_types=("MP", "PI", "PA"),
        warehouse=None,
    )
    assert "SUM(quantity)" in totals
    assert "SUM(stock_value)" in totals
    assert "COUNT_BIG(1) AS item_count" in totals
    assert params == ["20260930", "02", "MP", "PI", "PA"]

    by_type, _ = stock_inventory_sql.build_summary_by_type_query(
        snapshot_date="20260930",
        branches=("02",),
        product_types=None,
        warehouse=None,
    )
    assert "GROUP BY product_type" in by_type
    by_wh, _ = stock_inventory_sql.build_summary_by_warehouse_query(
        snapshot_date="20260930",
        branches=("02",),
        product_types=None,
        warehouse=None,
    )
    assert "GROUP BY branch_code, warehouse" in by_wh
