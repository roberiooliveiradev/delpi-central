from app.domain.totvs.protheus_customer_center import (
    CUSTOMER_CENTER_ALIAS,
    customer_center_assignments_sql,
    customer_center_catalog_label,
    customer_center_catalog_sql,
    customer_center_exists_predicate,
    customer_center_in_predicate,
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


def test_customer_center_catalog_groups_distinct_centers():
    sql = customer_center_catalog_sql(customer_code_filter_sql="1 = 1")
    upper = sql.upper()
    assert "A7_XCENT" in upper
    assert "GROUP BY" in upper
    assert "RTRIM(ISNULL(A7.A7_XCENT, '')) <> ''" in sql
    assert "A1_NREDUZ" in upper
    assert "WEG DRIVES" not in sql
    assert "1100" not in sql
    assert "1320" not in sql


def test_customer_center_catalog_label_uses_store_name_not_a_unit_map():
    assert customer_center_catalog_label("1320", "WEG AUTOMACAO") == "WEG AUTOMACAO (1320)"
    assert customer_center_catalog_label("1100", "WEG MOTORES") != customer_center_catalog_label(
        "1200", "WEG MOTORES"
    )
    assert "WEG DRIVES" not in customer_center_catalog_label("1320", "WEG AUTOMACAO")


def test_customer_center_link_left_projects_without_becoming_a_filter():
    sql = customer_center_link_sql(
        product_column="C6.C6_PRODUTO",
        customer_column="C5.C5_CLIENTE",
        store_column="C5.C5_LOJACLI",
        join_type="left",
    )
    upper = sql.upper()
    assert "LEFT JOIN (" in upper
    assert "INNER JOIN (" not in upper
    assert "A7_XCENT" in upper
    assert "GROUP BY" in upper


def test_customer_center_assignments_group_code_store_and_center():
    sql = customer_center_assignments_sql(customer_code_filter_sql="1 = 1")
    upper = sql.upper()
    assert "A7_XCENT" in upper
    assert "A7_CLIENTE" in upper
    assert "A7_LOJA" in upper
    assert "GROUP BY" in upper
    assert "RTRIM(ISNULL(A7.A7_XCENT, '')) <> ''" in sql
    assert "1100" not in sql
    assert "1320" not in sql
    assert "WEG DRIVES" not in sql


def test_customer_center_in_predicate_omits_sql_when_filter_is_absent():
    sql, params = customer_center_in_predicate(None)
    assert sql == ""
    assert params == []


def test_customer_center_in_predicate_keeps_1320_out_of_1700():
    sql, params = customer_center_in_predicate(["1320"])
    assert "1700" not in sql
    assert params == ["1320"]
    assert "IN (?)" in sql


def test_customer_center_exists_predicate_groups_before_filtering():
    sql, params = customer_center_exists_predicate(["1320", "1505"])
    upper = sql.upper()
    assert "A7_XCENT" in upper
    assert "GROUP BY" in upper
    assert "1700" not in sql
    assert params == ["1320", "1505"]


def test_customer_center_catalog_empty_codes_predicate_excludes_rows():
    sql = customer_center_catalog_sql(customer_code_filter_sql="1 = 0")
    assert "1 = 0" in sql
    assert "A7_XCENT" in sql.upper()
