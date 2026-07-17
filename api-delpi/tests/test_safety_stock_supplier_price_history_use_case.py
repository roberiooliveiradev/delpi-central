from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockSupplierPriceHistoryRequest,
)
from app.application.use_cases.supplies.get_safety_stock_supplier_price_history_use_case import (
    GetSafetyStockSupplierPriceHistoryUseCase,
)


def test_supplier_price_history_use_case_filters_and_summarizes() -> None:
    repository = MagicMock()
    repository.fetch_purchase_price_history.return_value = [
        {
            "branch": "01",
            "entry_date": "20260710",
            "issue_date": "20260709",
            "supplier_code": "F001",
            "supplier_store": "01",
            "supplier_name": "ACME",
            "unit_price": 12.5,
            "quantity": 10,
            "total_value": 125,
            "invoice_number": "002",
            "invoice_series": "1",
        },
        {
            "branch": "01",
            "entry_date": "20260115",
            "issue_date": "20260114",
            "supplier_code": "F001",
            "supplier_store": "01",
            "supplier_name": "ACME",
            "unit_price": 10.0,
            "quantity": 5,
            "total_value": 50,
            "invoice_number": "001",
            "invoice_series": "1",
        },
    ]

    with patch(
        "app.application.use_cases.supplies.get_safety_stock_supplier_price_history_use_case.resolve_history_date_range",
        return_value=("20250717", "20260718"),
    ):
        result = GetSafetyStockSupplierPriceHistoryUseCase(repository).execute(
            SafetyStockSupplierPriceHistoryRequest(
                branch="01",
                product_code="10010005",
                supplier_code="F001",
                supplier_store="01",
            )
        )

    repository.fetch_purchase_price_history.assert_called_once_with(
        "10010005",
        "20250717",
        "20260718",
        branch="01",
        limit=500,
        supplier_code="F001",
        supplier_store="01",
        date_basis="entry",
    )
    assert result["total"] == 2
    assert result["items"][0]["unit_price"] == 10.0
    assert result["items"][-1]["unit_price"] == 12.5
    assert result["summary"]["variation_percent"] == 25.0


def test_supplier_price_history_request_requires_store() -> None:
    try:
        SafetyStockSupplierPriceHistoryRequest(
            branch="01",
            product_code="10010005",
            supplier_code="F001",
            supplier_store="",
        )
        raise AssertionError("esperado ValueError")
    except ValueError as exc:
        assert "loja" in str(exc).lower()
