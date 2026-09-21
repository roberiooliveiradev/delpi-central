from app.domain.totvs.protheus_customer_center import (
    CUSTOMER_CENTER_ALIAS,
    CUSTOMER_CENTER_MASTER_ALIAS,
    UNCLASSIFIED_CUSTOMER_CENTER_NAME,
    customer_center_active_expr,
    customer_center_classification_join_sql,
    customer_center_link_sql,
    customer_center_master_join_sql,
    customer_center_name_expr,
)


def test_customer_center_link_groups_sa7_before_joining():
    sql = customer_center_link_sql(
        product_column="C6.C6_PRODUTO",
        customer_column="C5.C5_CLIENTE",
        store_column="C5.C5_LOJACLI",
    )
    upper = sql.upper()
    assert "A7_XCENT" in upper
    assert "GROUP BY" in upper
    assert upper.count("SA7010") == 1
    assert upper.find("FROM SA7010") < upper.find("GROUP BY")
    assert "INNER JOIN (" in upper
    assert CUSTOMER_CENTER_ALIAS in sql
    assert "C6.C6_PRODUTO" in sql
    assert "A7_FILIAL" not in upper


def test_classification_join_keeps_unclassified_lines():
    sql = customer_center_classification_join_sql(
        product_column="D2.D2_COD",
        customer_column="D2.D2_CLIENTE",
        store_column="D2.D2_LOJA",
    )
    upper = sql.upper()
    assert "LEFT JOIN (" in upper
    assert "SA7010" in upper
    assert "A7_XCENT" in upper
    assert "<> ''" not in sql
    assert "D2.D2_COD" in sql
    assert "A7_FILIAL" not in upper


def test_center_master_joins_by_customer_store_and_code():
    sql = customer_center_master_join_sql()
    upper = sql.upper()
    assert "ZC0010" in upper
    assert "ZC0_CLIENT" in upper
    assert "ZC0_LOJA" in upper
    assert "ZC0_CODIGO" in upper
    assert CUSTOMER_CENTER_MASTER_ALIAS in sql
    assert f"{CUSTOMER_CENTER_ALIAS}.customer_code" in sql
    assert "ZC0_FILIAL" not in upper


def test_unclassified_name_and_inactive_master_expressions():
    name_sql = customer_center_name_expr()
    active_sql = customer_center_active_expr()
    assert UNCLASSIFIED_CUSTOMER_CENTER_NAME in name_sql
    assert "IN ('S', '1')" in active_sql
    assert "THEN NULL" in active_sql
