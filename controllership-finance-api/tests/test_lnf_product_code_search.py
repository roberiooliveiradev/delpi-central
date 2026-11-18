"""GLPI #814: busca paginada por código Delpi com proveniência dos itens NF-e."""
from __future__ import annotations

from unittest.mock import MagicMock

from controllership_finance_app.application.invoice_posting.unmapped_supplier_product_service import (
    indexed_nfe_product_rows,
)
from controllership_finance_app.infrastructure.invoice_posting.postgres_invoice_posting_repository import (
    PostgresInvoicePostingRepository,
)


def test_index_rows_only_when_issuer_and_mapping_are_verified() -> None:
    detail = {
        "productMapping": {"state": "ready"},
        "items": [
            {"supplierProductCode": "FORN-20", "internalProductCode": "90264242", "mappingStatus": "mapped"},
            {"supplierProductCode": "SEM", "internalProductCode": None, "mappingStatus": "unmapped"},
            {"supplierProductCode": "AMB", "internalProductCode": "90260001", "mappingStatus": "ambiguous"},
        ],
    }
    items = indexed_nfe_product_rows(detail, request_id="r-1")
    assert [(r["item_position"], r["internal_product_code"], r["mapping_status"]) for r in items] == [
        (1, "90264242", "mapped"),
        (2, None, "unmapped"),
        (3, None, "ambiguous"),
    ]
    assert indexed_nfe_product_rows(
        {**detail, "productMapping": {"state": "issuer_mismatch"}}, request_id="r-1"
    ) == []


def test_product_code_filters_before_count_and_pagination_without_join_duplicates() -> None:
    repo = PostgresInvoicePostingRepository(connection=MagicMock())
    statements = []

    def one(sql, params=None):
        statements.append((sql, params))
        return {"total": 0}

    def many(sql, params=None):
        statements.append((sql, params))
        return []

    repo.fetch_one = one
    repo.fetch_all = many
    repo.list_requests(
        filters={"branch": "02", "status": "", "product_code": "90264242"},
        created_by_user_id="person-1",
        page=2,
        page_size=20,
    )
    assert len(statements) == 2
    count_sql, count_params = statements[0]
    list_sql, list_params = statements[1]
    for sql in (count_sql, list_sql):
        assert "EXISTS (" in sql
        assert "invoice_posting_request_products" in sql
        assert "invoice_posting_request_linked_po_lines" in sql
        assert "invoice_posting_requests.id" in sql
        assert "created_by_user_id = %s" in sql
        assert "branch_code = %s" in sql
        assert "upper(btrim(ip.internal_product_code)) = upper(%s)" in sql
        assert "upper(btrim(ll.product_code)) = upper(%s)" in sql
    assert count_params == ("person-1", "02", "90264242", "90264242")
    assert list_params == ("person-1", "02", "90264242", "90264242", 20, 20)


def test_no_product_filter_keeps_original_list_query_and_pagination() -> None:
    repo = PostgresInvoicePostingRepository(connection=MagicMock())
    statements = []
    repo.fetch_one = lambda sql, params=None: (statements.append(sql) or {"total": 0})
    repo.fetch_all = lambda sql, params=None: (statements.append(sql) or [])
    repo.list_requests(filters={}, created_by_user_id=None, page=1, page_size=20)
    assert all("invoice_posting_request_products" not in sql for sql in statements)
