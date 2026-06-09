from unittest.mock import MagicMock

import pytest

from app.application.dto.product.product_raw_material_price_request import (
    ProductRawMaterialPriceRequest,
)
from app.application.services.product import product_raw_material_price_service as service
from app.application.use_cases.product.get_product_raw_material_price_use_cases import (
    GetProductLastPurchaseUseCase,
    GetProductRawMaterialPriceIntelligenceUseCase,
)


def test_enrich_price_history_variation_percent() -> None:
    items = [
        {"unit_price": 10.0},
        {"unit_price": 8.0},
    ]

    enriched = service.enrich_price_history_with_variation(items)

    assert enriched[0]["variation_percent"] == pytest.approx(25.0)
    assert enriched[1]["variation_percent"] is None


def test_classify_price_status_stable() -> None:
    status = service.classify_price_status(
        price_history=[{"variation_percent": 1.0}],
        last_purchase={"unit_price": 10},
    )
    assert status == "ESTAVEL"


def test_classify_price_status_increase() -> None:
    status = service.classify_price_status(
        price_history=[{"variation_percent": 5.0}],
        last_purchase={"unit_price": 10},
    )
    assert status == "ALTA DE PRECO"


def test_build_intelligence_includes_warnings_for_non_mp() -> None:
    result = service.build_raw_material_price_intelligence(
        product={"product_type": "PA", "registered_last_purchase_price": 1},
        last_purchase=None,
        price_history_raw=[],
        budget_history_raw=[],
        date_start="20250101",
        date_end_exclusive="20260101",
        branch=None,
    )

    assert result["warnings"]
    assert result["price_status"] == "SEM HISTORICO DE COMPRA"


def test_last_purchase_use_case() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {
        "product_code": "10080001",
        "product_type": "MP",
    }
    repository.fetch_last_purchase.return_value = {
        "supplier_code": "000002",
        "unit_price": 0.089,
    }

    result = GetProductLastPurchaseUseCase(repository).execute(
        ProductRawMaterialPriceRequest(code="10080001")
    )

    assert result["last_purchase"]["supplier_code"] == "000002"


def test_intelligence_use_case_composite() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {
        "product_code": "10080001",
        "product_type": "MP",
        "registered_last_purchase_price": 0.08,
    }
    repository.fetch_last_purchase.return_value = {
        "unit_price": 0.089,
        "supplier_code": "000002",
    }
    repository.fetch_purchase_price_history.return_value = [
        {"unit_price": 0.089, "supplier_code": "000002"},
        {"unit_price": 0.088, "supplier_code": "000002"},
    ]
    repository.fetch_purchase_budget_history.return_value = [
        {"source": "SC7010", "unit_price": 0.089},
    ]

    result = GetProductRawMaterialPriceIntelligenceUseCase(repository).execute(
        ProductRawMaterialPriceRequest(code="10080001", history_limit=12)
    )

    assert result["product"]["product_code"] == "10080001"
    assert result["last_purchase"]["unit_price"] == 0.089
    assert len(result["price_history"]["items"]) == 2
    assert result["budget_history"]["summary"]["total_purchase_orders"] == 1
    assert result["indicators"]["dominant_supplier_code"] == "000002"
