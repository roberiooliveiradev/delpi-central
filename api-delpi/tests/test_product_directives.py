from unittest.mock import MagicMock

import pytest

from app.application.dto.product.product_directives_request import ProductDirectivesRequest
from app.application.services.product import product_directives_service as service
from app.application.use_cases.product.get_product_directives_use_case import (
    GetProductDirectivesUseCase,
)
from app.domain.services.product.product_identifier_resolution_service import (
    ProductIdentifierResolutionService,
)


def test_normalize_identifier_strips_non_digits() -> None:
    assert ProductIdentifierResolutionService.normalize_identifier("10.018.137") == "10018137"


def test_resolve_prefers_delpi_code_when_9026_prefix() -> None:
    resolved = ProductIdentifierResolutionService.resolve(
        "90260882",
        by_code={
            "product_code": "90260882",
            "description": "PA TESTE",
            "product_type": "PA",
            "customer_reference": "10018137",
            "unit": "UN",
            "group_code": "9026",
        },
        by_customer_reference=None,
    )

    assert resolved is not None
    assert resolved.identifier_type == "delpi_code"
    assert resolved.product_code == "90260882"
    assert resolved.customer_reference == "10018137"


def test_resolve_uses_customer_reference_for_non_delpi_identifier() -> None:
    resolved = ProductIdentifierResolutionService.resolve(
        "10018137",
        by_code=None,
        by_customer_reference={
            "product_code": "90260882",
            "description": "PA TESTE",
            "product_type": "PA",
            "customer_reference": "10018137",
            "unit": "UN",
            "group_code": "9026",
        },
    )

    assert resolved is not None
    assert resolved.identifier_type == "customer_reference"
    assert resolved.product_code == "90260882"


def test_build_raw_material_entries_enriches_suppliers_and_last_purchase() -> None:
    structure_items = [
        {
            "component_type": "PI",
            "component_code": "50230070",
            "component_description": "PI TESTE",
            "level": 1,
        },
        {
            "component_type": "MP",
            "component_code": "10080001",
            "component_description": "MP TESTE",
            "component_unit": "KG",
            "component_group": "1008",
            "level": 2,
            "parent_code": "50230070",
            "quantity_per": "1",
            "accumulated_quantity": "2",
            "path": "90260882 > 50230070 > 10080001",
        },
    ]

    payload = service.build_product_directives_payload(
        resolved=ProductIdentifierResolutionService.resolve(
            "90260882",
            by_code={
                "product_code": "90260882",
                "description": "PA TESTE",
                "product_type": "PA",
                "customer_reference": "10018137",
                "unit": "UN",
                "group_code": "9026",
            },
            by_customer_reference=None,
        ),
        structure_items=structure_items,
        suppliers_rows=[
            {
                "product_code": "10080001",
                "supplier_code": "000002",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR A",
                "supplier_part_number": "PN-123",
            }
        ],
        last_purchase_rows=[
            {
                "product_code": "10080001",
                "invoice_number": "000123",
                "supplier_code": "000002",
                "supplier_part_number": "PN-123",
                "unit_price": 0.89,
            }
        ],
    )

    assert payload["resolution"]["delpi_code"] == "90260882"
    assert payload["summary"]["total_raw_material_entries"] == 1
    assert payload["raw_materials"][0]["suppliers"][0]["supplier_part_number"] == "PN-123"
    assert payload["raw_materials"][0]["last_purchase"]["invoice_number"] == "000123"


def test_directives_use_case_not_found() -> None:
    product_repository = MagicMock()
    product_repository.fetch_product_by_code.return_value = None
    product_repository.fetch_product_by_customer_reference.return_value = None

    result = GetProductDirectivesUseCase(
        product_repository=product_repository,
        playbook_repository=MagicMock(),
        suppliers_repository=MagicMock(),
        price_repository=MagicMock(),
    ).execute(ProductDirectivesRequest(identifier="99999999"))

    assert result["product"] is None


def test_directives_use_case_orchestrates_repositories() -> None:
    product_repository = MagicMock()
    product_repository.fetch_product_by_code.return_value = {
        "product_code": "90260882",
        "description": "PA TESTE",
        "product_type": "PA",
        "customer_reference": "10018137",
        "unit": "UN",
        "group_code": "9026",
    }
    product_repository.fetch_product_by_customer_reference.return_value = None

    playbook_repository = MagicMock()
    playbook_repository.fetch_structure_with_exclusivity.return_value = [
        {
            "component_type": "MP",
            "component_code": "10080001",
            "component_description": "MP TESTE",
            "level": 1,
        }
    ]

    suppliers_repository = MagicMock()
    suppliers_repository.list_suppliers_for_codes.return_value = []

    price_repository = MagicMock()
    price_repository.fetch_last_purchases_for_codes.return_value = []

    result = GetProductDirectivesUseCase(
        product_repository=product_repository,
        playbook_repository=playbook_repository,
        suppliers_repository=suppliers_repository,
        price_repository=price_repository,
    ).execute(ProductDirectivesRequest(identifier="90260882"))

    playbook_repository.fetch_structure_with_exclusivity.assert_called_once_with("90260882", 50)
    suppliers_repository.list_suppliers_for_codes.assert_called_once_with(["10080001"])
    price_repository.fetch_last_purchases_for_codes.assert_called_once_with(
        ["10080001"],
        branch=None,
    )
    assert result["product"]["product_code"] == "90260882"
