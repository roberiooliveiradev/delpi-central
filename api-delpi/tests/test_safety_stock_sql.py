from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    INTERNAL_TRANSFER_SUPPLIER_CODES,
    PRIMARY_WAREHOUSE,
    WORK_IN_PROCESS_WAREHOUSES,
    build_where_clauses,
    linked_suppliers_sql,
    materials_base_cte,
    open_commitments_sql,
    open_purchase_orders_sql,
    product_detail_sql,
    resolve_order_by,
    stock_agg_cte,
)


def test_stock_agg_cte_contains_required_filters() -> None:
    sql = stock_agg_cte()
    assert "SB2010" in sql
    assert "B2_FILIAL" in sql
    assert f"B2_LOCAL) = '{PRIMARY_WAREHOUSE}'" in sql
    assert "D_E_L_E_T_" in sql
    assert "WITH (NOLOCK)" in sql


def test_materials_base_cte_contains_mp_and_sbz_join() -> None:
    sql = materials_base_cte()
    assert "SB1010" in sql
    assert "SBZ010" in sql
    assert "B1_TIPO = 'MP'" in sql
    assert "BZ_FILIAL" in sql
    assert "BZ_ESTSEG" in sql
    assert "without_safety_stock" in sql
    assert "below_safety_stock" in sql
    assert "available_stock" in sql


def test_build_where_clauses_excludes_blocked_by_default() -> None:
    where_sql, params = build_where_clauses(
        include_blocked=False,
        product_group=None,
        unit=None,
        search=None,
        status=None,
        include_without_safety_stock=True,
    )
    assert "blocked_raw" in where_sql
    assert "B1_MSBLQL" not in where_sql
    assert params == []


def test_build_where_clauses_status_and_search_use_params() -> None:
    where_sql, params = build_where_clauses(
        include_blocked=True,
        product_group="GRP",
        unit="PC",
        search="parafuso",
        status="below_safety_stock",
        include_without_safety_stock=False,
    )
    assert "status = ?" in where_sql
    assert "product_group) = ?" in where_sql
    assert "unit) = ?" in where_sql
    assert "LIKE ?" in where_sql
    assert "without_safety_stock" in where_sql
    assert params == ["GRP", "PC", "%parafuso%", "%parafuso%", "below_safety_stock"]


def test_resolve_order_by_allowlist() -> None:
    assert resolve_order_by("primary_stock", "desc") == "available_stock DESC, product_code ASC"
    assert resolve_order_by("product_code", "asc") == "product_code ASC"
    assert resolve_order_by("unknown", "asc") == "product_code ASC"


def test_work_in_process_warehouses_include_99() -> None:
    assert "99" in WORK_IN_PROCESS_WAREHOUSES
    sql = stock_agg_cte()
    assert "warehouse_99_stock" in sql


def test_open_purchase_orders_sql_filters_residue_and_open_balance() -> None:
    sql = open_purchase_orders_sql()
    assert "SC7010" in sql
    assert "C7_RESIDUO" in sql
    assert "C7_QUANT > SC7.C7_QUJE" in sql
    assert "SA2010" in sql
    assert "C7_QTDACLA" in sql


def test_product_detail_sql_includes_conversion_fields() -> None:
    sql = product_detail_sql()
    assert "available_stock" in sql
    assert "B1_SEGUM" in sql
    assert "B1_CONV" in sql
    assert "B1_TIPCONV" in sql


def test_open_commitments_sql_filters_open_balance_and_uses_qtdeori() -> None:
    sql = open_commitments_sql()
    assert "SD4010" in sql
    assert "D4_QUANT > 0" in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert "D4_QTDEORI" in sql
    assert "D4_QTDORI" not in sql
    assert "D4_FILIAL =" in sql
    assert "D4_COD =" in sql
    assert "WITH (NOLOCK)" in sql
    assert "RTRIM(SD4.D4_FILIAL) =" not in sql
    # SD4010 não possui D4_UM — a UM do empenho é a primária do produto (B1_UM)
    assert "D4_UM" not in sql
    assert "B1_UM" in sql


def test_linked_suppliers_sql_uses_sa5_sa2_sd1_and_last_purchase_rules() -> None:
    sql = linked_suppliers_sql()
    assert "SA5010" in sql
    assert "SA2010" in sql
    assert "SD1010" in sql
    assert "A5_PRODUTO" in sql
    assert "A5_FORNECE" in sql
    assert "A5_CODPRF" in sql
    assert "supplier_part_number" in sql
    assert "A2_NREDUZ" in sql
    assert "A2_NOME" in sql
    assert "A2_CGC" in sql
    assert "D1_VUNIT" in sql
    assert "D1_TOTAL" in sql
    assert "D1_DTDIGIT" in sql
    assert "D1_TIPO = 'N'" in sql
    assert "D1_QUANT > 0" in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert "ROW_NUMBER()" in sql
    assert "D1_DTDIGIT DESC" in sql
    assert "D1_EMISSAO DESC" in sql
    assert "R_E_C_N_O_ DESC" in sql
    assert "LEFT JOIN last_purchase" in sql
    assert "WITH (NOLOCK)" in sql
    assert sql.count("?") == 5


def test_linked_suppliers_sql_orders_by_last_purchase_desc_without_purchase_last() -> None:
    sql = linked_suppliers_sql()
    order_by_clause = sql.split("ORDER BY", 1)[1]
    assert "CASE WHEN LP.product_code IS NULL THEN 1 ELSE 0 END" in order_by_clause
    assert "LP.last_purchase_date DESC" in order_by_clause
    assert order_by_clause.index("LP.product_code IS NULL") < order_by_clause.index(
        "last_purchase_date DESC"
    )


def test_linked_suppliers_sql_excludes_internal_transfer_suppliers() -> None:
    """Cadastros DELPI de transferência entre filiais não são fornecedores reais."""
    sql = linked_suppliers_sql()
    assert "A5_FORNECE) NOT IN" in sql
    for code in INTERNAL_TRANSFER_SUPPLIER_CODES:
        assert f"'{code}'" in sql
    assert "000052" in sql
    assert "000972" in sql
