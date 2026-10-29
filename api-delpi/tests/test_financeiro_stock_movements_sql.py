"""SQL builders for the R05 stock-movements summary (MATR320 rule).

Guards the canonical classification (BR-R05-003/004/005), the bound
parameters, the DECIMAL(30,9) per-line precision (BR-R05-012) and the
scope/sibling-branch filter application.
"""

from __future__ import annotations

from app.infrastructure.persistence.totvs.financeiro_stock_movements import (
    stock_movements_sql,
)


def test_sd1_query_binds_branches_window_and_types() -> None:
    sql, params = stock_movements_sql.build_sd1_by_type_query(
        branches=("01", "02"),
        period_start="20260901",
        period_end="20260930",
        product_types=("MP", "PI", "PA"),
    )
    assert "SD1010" in sql
    assert "D1.D1_DTDIGIT BETWEEN ? AND ?" in sql
    assert "D1.D1_ORIGLAN <> 'LF'" in sql
    assert "TES.estoque = 'S'" in sql
    assert "CAST(D1.D1_CUSTO AS DECIMAL(30,9))" in sql
    # purchases/sales_returns/third_party_in split on poder3 + tipo
    assert "purchases" in sql
    assert "sales_returns" in sql
    assert "third_party_in" in sql
    assert params == ["01", "02", "20260901", "20260930", "MP", "PI", "PA"]


def test_sd2_query_binds_window_and_uses_emissao() -> None:
    sql, params = stock_movements_sql.build_sd2_by_type_query(
        branches=("01",),
        period_start="20260901",
        period_end="20260930",
        product_types=None,
    )
    assert "SD2010" in sql
    assert "D2.D2_EMISSAO BETWEEN ? AND ?" in sql
    assert "D2.D2_ORIGLAN <> 'LF'" in sql
    assert "sales" in sql
    assert "purchase_returns" in sql
    assert "third_party_out" in sql
    assert params == ["01", "20260901", "20260930"]


def test_sd3_classification_order_is_the_rule() -> None:
    """BR-R05-005 precedence must stay: PR* → production, RE4/DE4 →
    transfers, empty-OP non-3rd-party → internal, filled OP →
    requisition, remainder → process memo."""
    sql, params = stock_movements_sql.build_sd3_by_type_query(
        branches=("01", "02"),
        period_start="20260901",
        period_end="20260930",
        product_types=None,
    )
    production = sql.index("LIKE 'PR%' THEN 'production'")
    transfers = sql.index("IN ('RE4', 'DE4') THEN 'transfers'")
    internal = sql.index("THEN 'internal'")
    requisition = sql.index("THEN 'requisition'")
    memo = sql.index("ELSE 'process_memo'")
    assert production < transfers < internal < requisition < memo
    assert "D3.D3_ESTORNO <> 'S'" in sql
    # Signed value: TM > 500 negates the cost before aggregating.
    assert "D3.D3_TM > '500'" in sql
    assert "-CAST(D3.D3_CUSTO1 AS DECIMAL(30,9))" in sql
    assert params == ["01", "02", "20260901", "20260930"]


def test_sd3_type_filter_applies_on_outer_select() -> None:
    sql, params = stock_movements_sql.build_sd3_by_type_query(
        branches=("01",),
        period_start="20260901",
        period_end="20260930",
        product_types=("MP",),
    )
    assert "WHERE product_type IN (?)" in sql
    assert params == ["01", "20260901", "20260930", "MP"]


def test_no_type_filter_when_scope_is_all_products() -> None:
    for builder in (
        stock_movements_sql.build_sd1_by_type_query,
        stock_movements_sql.build_sd2_by_type_query,
        stock_movements_sql.build_sd3_by_type_query,
    ):
        sql, params = builder(
            branches=("01",),
            period_start="20260901",
            period_end="20260930",
            product_types=None,
        )
        assert "B1_TIPO) IN" not in sql
        assert "product_type IN" not in sql


def test_tes_join_prefers_branch_specific_register() -> None:
    sql, _ = stock_movements_sql.build_sd1_by_type_query(
        branches=("01",),
        period_start="20260901",
        period_end="20260930",
        product_types=None,
    )
    assert "F4.F4_CODIGO = D1.D1_TES" in sql
    assert "SELECT TOP 1" in sql
