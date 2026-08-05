"""Regressão: consulta SC7 de pedidos abertos no LNF."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_invoice_posting_sc7_repository import (
    TotvsInvoicePostingSc7Repository,
)


def _opened_repo() -> TotvsInvoicePostingSc7Repository:
    repo = TotvsInvoicePostingSc7Repository()
    repo.connection = object()
    repo.cursor = object()
    repo._connect = lambda: None  # type: ignore[method-assign]
    repo._close = lambda *a, **k: None  # type: ignore[method-assign]
    return repo


@patch.object(TotvsInvoicePostingSc7Repository, "execute_query")
def test_list_open_purchase_orders_by_supplier_builds_sql_and_params(
    mock_execute_query: MagicMock,
) -> None:
    mock_execute_query.return_value = [
        {
            "branch": "01",
            "order_number": "000123",
            "order_item": "0001",
            "product_code": "10080001",
            "product_description": "Parafuso",
            "supplier_part_number": "PN-1",
            "warehouse": "01",
            "unit": "PC",
            "ordered_quantity": 10.0,
            "delivered_quantity": 2.0,
            "open_quantity": 8.0,
            "pre_invoice_quantity": 0.0,
            "issue_date": "20260701",
            "expected_delivery_date": "20260725",
            "supplier_code": "000001",
            "supplier_store": "01",
            "supplier_name": "Fornecedor SA",
            "unit_price": 1.5,
            "open_merchandise_value": 12.0,
            "open_ipi_value": 0.0,
            "open_freight_value": 0.0,
            "open_discount_value": 0.0,
            "open_value": 12.0,
        }
    ]

    rows = _opened_repo().list_open_purchase_orders_by_supplier(
        branch_code="01",
        supplier_code="000001",
        supplier_store="01",
    )

    sql, params = mock_execute_query.call_args.args
    assert isinstance(sql, str)
    assert "SC7010" in sql
    assert "C7_FORNECE) =" in sql
    assert "C7_LOJA) =" in sql
    assert "C7_PRODUTO) =" not in sql
    assert params == ["01", "000001", "01"]
    assert len(rows) == 1
    assert rows[0]["order_number"] == "000123"
    assert rows[0]["issue_date"] == "2026-07-01"
    assert rows[0]["expected_delivery_date"] == "2026-07-25"


def test_list_open_purchase_orders_by_supplier_requires_identity() -> None:
    assert (
        TotvsInvoicePostingSc7Repository().list_open_purchase_orders_by_supplier(
            branch_code="01",
            supplier_code="",
            supplier_store="01",
        )
        == []
    )
