from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
    build_purchase_orders_for_lines_sql,
    build_purchase_request_headers_count_sql,
    build_purchase_request_headers_page_sql,
    build_purchase_request_lines_filters,
    build_purchase_request_lines_for_request_numbers_sql,
    build_purchase_request_lines_list_sql,
    build_receipts_for_orders_sql,
    default_date_range,
)


def test_filters_include_branch_and_issue_date_window() -> None:
    where_clause, params = build_purchase_request_lines_filters(branch="02")
    assert "SC1.D_E_L_E_T_ = ''" in where_clause
    assert "C1_FILIAL" in where_clause
    assert "C1_EMISSAO" in where_clause
    assert "02" in params


def test_default_date_range_uses_90_days() -> None:
    start, end = default_date_range(date_from=None, date_to="2026-08-26", reference=__import__("datetime").date(2026, 8, 26))
    assert start == "2026-05-28"
    assert end == "2026-08-26"


def test_cost_centers_use_parameterized_in_clause() -> None:
    where_clause, params = build_purchase_request_lines_filters(
        branch="01",
        cost_centers=["0413", "0520"],
    )
    normalized = where_clause.replace(" ", "")
    assert "C1_CC)IN(?,?)" in normalized or "C1_CC)IN(?,?)" in normalized.replace("RTRIM(", "")
    assert "0413" in params and "0520" in params
    assert params.count("0413") == 1
    assert params.count("0520") == 1


def test_list_sql_orders_by_issue_date_and_request_number() -> None:
    sql = build_purchase_request_lines_list_sql(where_clause="1=1", offset=0, page_size=50)
    assert "C1_EMISSAO DESC" in sql
    assert "C1_NUM DESC" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql


def test_sc7_join_uses_numsc_and_itemsc_not_pedido() -> None:
    sql, _ = build_purchase_orders_for_lines_sql([("02", "164708", "0001")])
    assert "C7_NUMSC" in sql
    assert "C7_ITEMSC" in sql
    assert "C1_PEDIDO" not in sql
    assert "C7_NUM = SC1.C1_PEDIDO" not in sql


def test_sd1_join_uses_d1_itempc_not_d1_item() -> None:
    sql, _ = build_receipts_for_orders_sql(
        [("02", "041446", "0001", "000001", "01", "90012345")]
    )
    assert "D1_ITEMPC" in sql
    assert "D1_FILIAL" in sql
    assert "D1_PEDIDO" in sql
    assert "D1_ITEM = C7_ITEM" not in sql


def test_supplier_filter_uses_sc7_numsc_itemsc_join() -> None:
    where_clause, _ = build_purchase_request_lines_filters(
        branch="01",
        supplier_code="000001",
    )
    assert "C7_NUMSC" in where_clause
    assert "C7_ITEMSC" in where_clause
    assert "C1_PEDIDO" not in where_clause


def test_headers_count_uses_distinct_request_grain() -> None:
    where_clause, _ = build_purchase_request_lines_filters(branch="01")
    sql = build_purchase_request_headers_count_sql(where_clause)
    assert "SELECT DISTINCT" in sql
    assert "request_number" in sql
    assert "visible_requests" in sql


def test_headers_page_groups_and_orders_by_issue_date() -> None:
    where_clause, _ = build_purchase_request_lines_filters(branch="02")
    sql = build_purchase_request_headers_page_sql(where_clause=where_clause)
    assert "GROUP BY" in sql
    assert "MIN(RTRIM(SC1.C1_EMISSAO)) DESC" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql


def test_multi_unit_uses_parameterized_in_clause() -> None:
    where_clause, params = build_purchase_request_lines_filters(branches=["01", "02"])
    assert "C1_FILIAL" in where_clause
    assert "IN" in where_clause
    assert params[:2] == ["01", "02"]


def test_cost_center_scopes_are_tuple_aware() -> None:
    where_clause, params = build_purchase_request_lines_filters(
        branches=["01", "02"],
        cost_center_scopes=["01:0413", "02:0520"],
    )
    assert "C1_CC" in where_clause
    assert "01" in params and "0413" in params
    assert "02" in params and "0520" in params
    assert where_clause.count("C1_FILIAL") >= 2


def test_sort_allowlist_includes_item_and_product_fields() -> None:
    from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
        PURCHASE_REQUESTS_SORT_FIELDS,
        resolve_purchase_requests_order_by,
    )

    assert "request_item" in PURCHASE_REQUESTS_SORT_FIELDS
    assert "product_code" in PURCHASE_REQUESTS_SORT_FIELDS
    assert "product_description" in PURCHASE_REQUESTS_SORT_FIELDS
    assert "overall_stage" not in PURCHASE_REQUESTS_SORT_FIELDS

    header_item = resolve_purchase_requests_order_by(
        sort_by="request_item", sort_dir="asc", grain="header"
    )
    assert "MIN(RTRIM(SC1.C1_ITEM))" in header_item
    assert "C1_NUM" in header_item and "C1_FILIAL" in header_item

    header_product = resolve_purchase_requests_order_by(
        sort_by="product_code", sort_dir="desc", grain="header"
    )
    assert "MIN(RTRIM(SC1.C1_PRODUTO))" in header_product

    header_desc = resolve_purchase_requests_order_by(
        sort_by="product_description", sort_dir="asc", grain="header"
    )
    assert "SC1.C1_DESCRI" in header_desc
    assert "SB1" not in header_desc

    line_item = resolve_purchase_requests_order_by(
        sort_by="request_item", sort_dir="asc", grain="line"
    )
    assert "RTRIM(SC1.C1_ITEM)" in line_item
    assert "C1_FILIAL" in line_item and "C1_NUM" in line_item and "C1_ITEM" in line_item

    line_desc = resolve_purchase_requests_order_by(
        sort_by="product_description", sort_dir="desc", grain="line"
    )
    assert "SB1.B1_DESC" in line_desc


def test_invalid_sort_is_rejected() -> None:
    from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
        resolve_purchase_requests_order_by,
    )

    try:
        resolve_purchase_requests_order_by(sort_by="overall_stage", grain="header")
        raise AssertionError("expected invalid sort")
    except ValueError as exc:
        assert "sort_by" in str(exc)

    try:
        resolve_purchase_requests_order_by(sort_by="not_a_field", grain="line")
        raise AssertionError("expected invalid sort")
    except ValueError as exc:
        assert "sort_by" in str(exc)


def test_lines_for_request_numbers_scopes_in_clause() -> None:
    where_clause, params = build_purchase_request_lines_filters(branch="02")
    sql, extra = build_purchase_request_lines_for_request_numbers_sql(
        where_clause=where_clause,
        request_numbers=["164708", "100"],
    )
    normalized = sql.replace(" ", "")
    assert "C1_NUM)IN(?,?)" in normalized
    assert extra == ["164708", "100"]
    assert "OFFSET" not in sql
