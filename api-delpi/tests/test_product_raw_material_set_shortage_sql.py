from __future__ import annotations

from app.domain.totvs.protheus_production_orders import (
    MOTHER_ORDER_KEY_PREFIX_LENGTH,
    MOTHER_ORDER_SEQUENCE,
    mother_order_key_sql,
)
from app.infrastructure.persistence.totvs.product_repositories.product_raw_material_set_shortage_sql import (
    mp_stock_batch_sql,
    open_commitments_batch_sql,
    open_mother_orders_sql,
    open_purchase_orders_batch_sql,
    placeholders_for,
    product_header_sql,
    raw_material_bom_sql,
)


def test_product_header_sql_binds_code() -> None:
    sql = product_header_sql()
    assert "SB1010" in sql
    assert "LTRIM(RTRIM(SB1.B1_COD)) = ?" in sql
    assert "WITH (NOLOCK)" in sql


def test_raw_material_bom_sql_filters_mp_and_binds_depth() -> None:
    sql = raw_material_bom_sql()
    assert "SG1010" in sql
    assert "LTRIM(RTRIM(G1_COD)) = ?" in sql
    assert "bom_level < ?" in sql
    assert "B1_TIPO) = 'MP'" in sql
    assert "G1_INI" in sql
    assert "C1_" not in sql


def test_open_mother_orders_sql_uses_canonical_sequence() -> None:
    sql, params = open_mother_orders_sql(branch="01")
    assert "SC2010" in sql
    assert "LTRIM(RTRIM(OP.C2_PRODUTO)) = ?" in sql
    assert f"C2_SEQUEN)) = '{MOTHER_ORDER_SEQUENCE}'" in sql
    assert "OP.C2_QUANT > OP.C2_QUJE" in sql
    assert "OP.C2_DATRF" in sql
    assert "C2_FILIAL" in sql
    assert "WITH (NOLOCK)" in sql
    assert params == ["01"]


def test_mp_stock_batch_uses_available_warehouses_and_in_list() -> None:
    sql, params = mp_stock_batch_sql(branch="01", product_codes=["10080001", "10080022"])
    assert "SB2010" in sql
    assert "B2_LOCAL) IN ('01', '98', '99')" in sql
    assert "BZ_ESTSEG" in sql
    assert sql.count("IN (?, ?)") == 3
    assert params.count("10080001") == 3
    assert params.count("01") == 2


def test_open_purchase_orders_batch_excludes_residue() -> None:
    sql, params = open_purchase_orders_batch_sql(
        branch="02", placeholders=placeholders_for(["10080001"])
    )
    assert "SC7010" in sql
    assert "C7_RESIDUO" in sql
    assert "C7_QUANT > SC7.C7_QUJE" in sql
    assert "C1_" not in sql
    assert "IN (?)" in sql
    assert params == ["02"]


def test_open_commitments_batch_uses_canonical_mother_key() -> None:
    sql, params = open_commitments_batch_sql(
        branch="01", placeholders=placeholders_for(["10080001"])
    )
    expected_mother = mother_order_key_sql("RTRIM(SD4.D4_OP)")
    assert expected_mother in sql
    assert f"LEFT(RTRIM(SD4.D4_OP), {MOTHER_ORDER_KEY_PREFIX_LENGTH})" in sql
    assert f"+ '{MOTHER_ORDER_SEQUENCE}'" in sql
    assert "LEFT(RTRIM(SD4.D4_OP), 6) + '01001'" not in sql
    assert "D4_QUANT > 0" in sql
    assert "C2_DATPRI" in sql
    assert params == ["01"]
