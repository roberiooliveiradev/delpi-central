"""SQL builders: snapshot filters, logical delete, SB1 join, aggregation."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.financeiro_stock_inventory import (
    stock_inventory_sql,
    work_in_process_sql,
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


def test_p7_totals_split_by_process_warehouse():
    query, params = stock_inventory_sql.build_p7_totals_query(
        snapshot_date="20260930",
        branches=("01", "02"),
        product_types=None,
        process_warehouse="99",
    )
    # EM ESTOQUE (<> 99) + physical WIP (= 99) split over the same
    # grouped universe — one query, one population.
    assert "warehouse <> ?" in query
    assert "warehouse = ?" in query
    assert "process_physical_value" in query
    assert "stock_value" in query
    # Report-level: the warehouse item filter is not part of the query.
    assert "RTRIM(S.B9_LOCAL) = ?" not in query
    # CASE placeholders are textual before the grouped subquery.
    assert params == ["99", "99", "99", "20260930", "01", "02"]


def test_p7_totals_scope_filter_is_product_type_only():
    query, params = stock_inventory_sql.build_p7_totals_query(
        snapshot_date="20260930",
        branches=("01",),
        product_types=("MP", "PI", "PA"),
        process_warehouse="99",
    )
    assert "P.B1_TIPO IN (?, ?, ?)" in query
    assert params == ["99", "99", "99", "20260930", "01", "MP", "PI", "PA"]


def test_wip_query_matr989_rule():
    query, params = work_in_process_sql.build_work_in_process_by_type_query(
        branches=("01", "02"),
        product_types=None,
        movement_cutoff="20260930",
        op_alive_cutoff="20261001",
    )
    # RE* adds, DE* subtracts, capped at the movement cutoff.
    assert "D3.D3_CF LIKE ?" in query
    assert "D3.D3_EMISSAO <= ?" in query
    assert "SD3010" in query
    # OP alive at emission: no PR* up to the cutoff and not
    # cancelled-without-producing in SC2.
    assert "SC2010" in query
    assert "C2.C2_QUJE = 0" in query
    assert "C2.C2_DATRF <= ?" in query
    assert "P3.D3_EMISSAO <= ?" in query
    assert "D_E_L_E_T_ = ' '" in query
    # Value CASE (RE%/DE%) then quantity CASE (RE%/DE%) precede the
    # branch list — the CTE binds both CASE pairs first.
    assert params[:4] == ["RE%", "DE%", "RE%", "DE%"]
    assert params[4:6] == ["01", "02"]
    assert "20260930" in params
    assert params.count("20261001") == 2


def test_wip_query_scope_filter_matches_snapshot_engine():
    query, params = work_in_process_sql.build_work_in_process_by_type_query(
        branches=("01",),
        product_types=("MP", "PI", "PA"),
        movement_cutoff="20260930",
        op_alive_cutoff="20261001",
    )
    assert "RTRIM(P.B1_TIPO) IN (?, ?, ?)" in query
    assert params[-3:] == ["MP", "PI", "PA"]
