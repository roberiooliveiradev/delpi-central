from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.supplies.safety_stock_request import SafetyStockItemDetailsRequest
from app.application.use_cases.supplies.get_safety_stock_item_suppliers_use_case import (
    GetSafetyStockItemSuppliersUseCase,
)


def test_suppliers_use_case_returns_collection_block() -> None:
    repository = MagicMock()
    repository.fetch_linked_suppliers.return_value = [
        {
            "product_code": "10010005",
            "supplier_code": "F001",
            "supplier_store": "01",
            "trade_name": "ACME",
            "legal_name": "ACME LTDA",
            "document": "12345678000199",
            "has_last_purchase": True,
            "last_purchase_date": "2026-07-10",
            "last_unit_price": 12.5,
            "last_quantity": 10.0,
            "last_total_value": 125.0,
            "last_invoice_number": "000123",
            "last_invoice_series": "1",
        },
        {
            "product_code": "10010005",
            "supplier_code": "F002",
            "supplier_store": "01",
            "trade_name": "BETA",
            "legal_name": "BETA SA",
            "document": "99887766000155",
            "has_last_purchase": False,
            "last_purchase_date": None,
            "last_unit_price": None,
            "last_quantity": None,
            "last_total_value": None,
            "last_invoice_number": None,
            "last_invoice_series": None,
        },
    ]

    result = GetSafetyStockItemSuppliersUseCase(repository).execute(
        SafetyStockItemDetailsRequest(branch="01", product_code="10010005")
    )

    repository.fetch_linked_suppliers.assert_called_once_with(
        branch="01",
        product_code="10010005",
    )
    assert result["total"] == 2
    assert result["items"][0]["last_unit_price"] == 12.5
    assert result["items"][1]["has_last_purchase"] is False


def test_suppliers_use_case_returns_empty_collection() -> None:
    repository = MagicMock()
    repository.fetch_linked_suppliers.return_value = []

    result = GetSafetyStockItemSuppliersUseCase(repository).execute(
        SafetyStockItemDetailsRequest(branch="02", product_code="MISSING")
    )

    assert result == {"items": [], "total": 0}
