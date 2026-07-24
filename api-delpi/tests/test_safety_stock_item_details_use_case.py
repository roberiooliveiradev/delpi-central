from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockItemDetailsRequest,
    peer_branch_for,
)
from app.application.use_cases.supplies.get_safety_stock_item_details_use_case import (
    GetSafetyStockItemDetailsUseCase,
)


def test_peer_branch_for_swaps_01_and_02() -> None:
    assert peer_branch_for("01") == "02"
    assert peer_branch_for("02") == "01"
    assert peer_branch_for("99") is None


def test_details_use_case_aggregates_coverage_commitments_and_projection() -> None:
    repository = MagicMock()
    repository.fetch_item_detail.side_effect = [
        {
            "product_code": "10010005",
            "product_description": "Parafuso",
            "product_type": "MP",
            "unit": "PC",
            "secondary_unit": "CX",
            "conversion_factor": 12.0,
            "conversion_type": "M",
            "product_group": "GRP",
            "branch": "01",
            "blocked": False,
            "status": "below_safety_stock",
            "safety_stock": 100.0,
            "available_stock": 40.0,
            "primary_stock": 30.0,
            "warehouse_50_stock": 0.0,
            "warehouse_98_stock": 5.0,
            "warehouse_99_stock": 5.0,
            "work_in_process_stock": 10.0,
            "work_in_process_committed": 0.0,
            "work_in_process_available": 10.0,
            "deficit_quantity": 60.0,
        },
        {
            "product_code": "10010005",
            "product_description": "Parafuso",
            "product_type": "MP",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "product_group": "GRP",
            "branch": "02",
            "blocked": False,
            "status": "above_safety_stock",
            "safety_stock": 50.0,
            "available_stock": 220.0,
            "primary_stock": 200.0,
            "warehouse_50_stock": 0.0,
            "warehouse_98_stock": 10.0,
            "warehouse_99_stock": 10.0,
            "work_in_process_stock": 0.0,
            "work_in_process_committed": 0.0,
            "work_in_process_available": 0.0,
            "deficit_quantity": 0.0,
        },
    ]
    repository.fetch_open_purchase_orders.return_value = [
        {
            "order_number": "PC001",
            "order_item": "01",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 50.0,
            "expected_delivery_date": "2026-08-10",
            "pre_invoice_quantity": 5.0,
            "supplier_name": "Fornecedor",
            "ordered_quantity": 50.0,
            "delivered_quantity": 0.0,
            "issue_date": "2026-07-01",
            "supplier_code": "F1",
            "supplier_store": "01",
            "unit_price": 1.5,
            "open_value": 75.0,
            "branch": "01",
            "product_code": "10010005",
            "product_description": "Parafuso",
        }
    ]
    repository.fetch_open_commitments.return_value = [
        {
            "branch": "01",
            "product_code": "10010005",
            "product_description": "Parafuso",
            "warehouse": "01",
            "production_order": "OP100",
            "origin_production_order": "",
            "commitment_date": "2026-07-20",
            "unit": "PC",
            "original_quantity": 30.0,
            "open_quantity": 20.0,
            "consumed_quantity": 10.0,
            "lot": "",
            "commitment_sequence": "001",
            "preserved_balance": 0.0,
        }
    ]
    repository.fetch_consumption_monthly_series.return_value = [
        {
            "year_month": "202601",
            "year_month_label": "2026-01",
            "consumption_quantity": 12.0,
            "movement_count": 2,
        }
    ]
    repository.fetch_last_consumption_date.return_value = "2025-11-20"
    repository.fetch_last_inventory_date.return_value = "2026-03-15"

    with patch(
        "app.domain.services.supplies.safety_stock_stock_projection_service._today",
        return_value=date(2026, 7, 16),
    ):
        result = GetSafetyStockItemDetailsUseCase(repository).execute(
            SafetyStockItemDetailsRequest(
                branch="01",
                product_code="10010005",
                peer_branch="02",
            )
        )

    assert result is not None
    assert result["purchase_coverage"]["status"] == "partial"
    assert result["purchase_coverage"]["eligible_open_quantity"] == 50.0
    assert result["purchase_coverage"]["remaining_to_buy"] == 10.0
    assert result["open_purchase_orders"]["total"] == 1
    assert result["open_purchase_orders"]["items"][0]["coverage_eligible"] is True
    assert result["open_purchase_orders"]["items"][0]["pre_invoice_quantity"] == 5.0
    assert result["open_commitments"]["total"] == 1
    assert result["open_commitments"]["items"][0]["projection_eligible"] is True
    assert result["open_commitments"]["summary"]["eligible_open_quantity"] == 20.0
    assert result["stock_projection"]["total"] >= 2
    assert result["stock_projection"]["summary"]["eligible_commitment_quantity"] == 20.0
    assert result["stock_projection"]["summary"]["eligible_purchase_quantity"] == 50.0
    assert result["stock_projection"]["items"][0]["origin"] == "initial_balance"
    assert result["monthly_consumption"]["total"] == 1
    assert result["monthly_consumption"]["period_consumption"] == 12.0
    assert "annual_comparison" in result
    assert result["peer_branch_stock"]["branch"] == "02"
    assert result["peer_branch_stock"]["found"] is True
    assert result["peer_branch_stock"]["available_stock"] == 220.0
    assert result["peer_branch_stock"]["last_consumption_date"] == "2025-11-20"
    assert result["stock"]["last_inventory_date"] == "2026-03-15"
    assert repository.fetch_item_detail.call_count == 2
    repository.fetch_last_consumption_date.assert_called_once_with(
        branch="02",
        product_code="10010005",
    )
    repository.fetch_last_inventory_date.assert_called_once_with(
        branch="01",
        product_code="10010005",
    )
    repository.fetch_consumption_monthly_series.assert_called_once()
