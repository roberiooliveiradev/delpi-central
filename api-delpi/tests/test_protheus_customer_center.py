from app.domain.totvs.protheus_customer_center import (
    CUSTOMER_CENTER_ALIAS,
    customer_center_link_sql,
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
