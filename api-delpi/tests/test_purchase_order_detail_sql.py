from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_repository import (
    compose_open_purchase_order,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    build_purchase_order_detail_sql,
    build_purchase_orders_list_filters,
    build_purchase_orders_list_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
    build_receipts_for_orders_sql,
)


def test_detail_filters_reuse_open_universe_and_order_number() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="01",
        order_number="041446",
    )
    assert "SC7.D_E_L_E_T_ = ''" in where_clause
    assert "C7_RESIDUO" in where_clause
    assert "C7_QUANT > SC7.C7_QUJE" in where_clause
    assert "RTRIM(SC7.C7_NUM) = ?" in where_clause
    assert "041446" in params
    assert "041446" not in where_clause
    assert "?" in where_clause


def test_detail_sql_includes_origin_buyer_and_no_offset() -> None:
    where_clause, _ = build_purchase_orders_list_filters(
        branch="02",
        order_number="000123",
    )
    sql = build_purchase_order_detail_sql(where_clause=where_clause)
    assert "SC7010" in sql
    assert "C7_COMPRA" in sql
    assert "C7_NUMSC" in sql
    assert "C7_ITEMSC" in sql
    assert "delivered_quantity" in sql
    assert "received_quantity" not in sql
    assert "OFFSET" not in sql
    list_sql = build_purchase_orders_list_sql(where_clause=where_clause)
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in list_sql
    assert "C7_NUMSC" not in list_sql


def test_detail_sql_parameterizes_branch_isolation() -> None:
    where_clause, params = build_purchase_orders_list_filters(
        branch="02",
        order_number="200001",
    )
    assert "C7_FILIAL" in where_clause
    assert "02" in params
    assert "200001" in params
    assert "02" not in where_clause.replace("C7_FILIAL", "")


def test_receipts_sql_uses_canonical_sd1_join_keys() -> None:
    sql, params = build_receipts_for_orders_sql(
        [("01", "041446", "0001", "000001", "01", "90012345")]
    )
    assert "D1_FILIAL" in sql
    assert "D1_PEDIDO" in sql
    assert "D1_ITEMPC" in sql
    assert "D1_FORNECE" in sql
    assert "D1_LOJA" in sql
    assert "D1_COD" in sql
    assert "D1_ITEM = C7_ITEM" not in sql
    assert params == ["01", "041446", "000001", "01", "90012345", "0001"]


def _line(
    *,
    order_item: str,
    supplier_code: str,
    product_code: str,
    source_request_number: str | None,
    source_request_item: str | None,
    expected_delivery_date: str = "20260920",
) -> dict:
    return {
        "branch": "01",
        "order_number": "000123",
        "order_item": order_item,
        "product_code": product_code,
        "product_description": "MP",
        "ordered_quantity": 10,
        "delivered_quantity": 4,
        "open_quantity": 6,
        "issue_date": "20260901",
        "expected_delivery_date": expected_delivery_date,
        "supplier_code": supplier_code,
        "supplier_store": "01",
        "supplier_name": f"Fornecedor {supplier_code}",
        "buyer_code": "COM01",
        "source_request_number": source_request_number,
        "source_request_item": source_request_item,
        "unit_price": 1.5,
        "open_value": 9.0,
    }


def test_compose_positive_open_po_with_receipts() -> None:
    rows = [
        _line(
            order_item="0001",
            supplier_code="A001",
            product_code="9001",
            source_request_number="164708",
            source_request_item="0001",
        )
    ]
    receipts = [
        {
            "branch": "01",
            "purchase_order_number": "000123",
            "purchase_order_item": "0001",
            "supplier_code": "A001",
            "supplier_store": "01",
            "product_code": "9001",
            "invoice_number": "NF1",
            "invoice_series": "1",
            "invoice_item": "01",
            "quantity": 4,
            "unit_price": 1.5,
            "total_value": 6.0,
            "invoice_issue_date": "20260910",
            "entry_date": "20260911",
        }
    ]
    result = compose_open_purchase_order(rows, receipts, today_protheus="20260916")
    assert result is not None
    assert result["branch"] == "01"
    assert result["order_number"] == "000123"
    assert "supplier" not in result
    assert "supplier_code" not in result
    item = result["items"][0]
    assert item["delivered_quantity"] == 4
    assert item["expected_delivery_date"] == "2026-09-20"
    assert item["source_request_number"] == "164708"
    assert item["receipts"][0]["invoice_number"] == "NF1"
    assert "received_quantity" not in item
    assert "payment_terms" not in result
    assert "currency" not in result


def test_compose_sibling_item_level_supplier_and_source_request() -> None:
    rows = [
        _line(
            order_item="0001",
            supplier_code="A001",
            product_code="9001",
            source_request_number="164708",
            source_request_item="0001",
        ),
        _line(
            order_item="0002",
            supplier_code="B002",
            product_code="9002",
            source_request_number="164900",
            source_request_item="0003",
            expected_delivery_date="20260901",
        ),
    ]
    receipts = [
        {
            "branch": "01",
            "purchase_order_number": "000123",
            "purchase_order_item": "0001",
            "supplier_code": "A001",
            "supplier_store": "01",
            "product_code": "9001",
            "invoice_number": "NF1",
            "invoice_series": "1",
            "invoice_item": "01",
            "quantity": 2,
            "unit_price": 1.5,
            "total_value": 3.0,
            "invoice_issue_date": "20260910",
            "entry_date": "20260911",
        }
    ]
    result = compose_open_purchase_order(rows, receipts, today_protheus="20260916")
    assert result is not None
    assert len(result["items"]) == 2
    first, second = result["items"]
    assert first["supplier_code"] == "A001"
    assert second["supplier_code"] == "B002"
    assert first["source_request_number"] == "164708"
    assert second["source_request_number"] == "164900"
    assert len(first["receipts"]) == 1
    assert second["receipts"] == []
    assert second["delivery_status"] == "late"


def test_compose_negative_empty_is_none() -> None:
    assert compose_open_purchase_order([], [], today_protheus="20260916") is None
