from unittest.mock import MagicMock

import pytest

from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.services.product import product_playbook_service as service
from app.application.use_cases.product.get_product_factory_status_use_case import (
    GetProductFactoryStatusUseCase,
)
from app.application.use_cases.product.get_product_production_status_use_case import (
    GetProductProductionStatusUseCase,
)
from app.application.services.product.protheus_field_normalizer import (
    normalize_playbook_payload,
)
from app.application.use_cases.product.get_product_structure_exclusivity_use_case import (
    GetProductStructureExclusivityUseCase,
)


def test_summarize_structure_counts_components() -> None:
    items = [
        {"component_type": "PI"},
        {"component_type": "MP", "exclusive_raw_material": "SIM"},
        {"component_type": "MP", "exclusive_raw_material": "NAO"},
    ]

    summary = service.summarize_structure(items)

    assert summary["total_components"] == 3
    assert summary["total_intermediates"] == 1
    assert summary["total_raw_materials"] == 2
    assert summary["total_exclusive_raw_materials"] == 1


def test_classify_factory_status_without_structure() -> None:
    status = service.classify_factory_status(
        has_structure=False,
        production_summary={},
        shipping_summary={},
        shipping_items=[],
    )

    assert status == "SEM ESTRUTURA VIGENTE"


def test_classify_factory_status_ready_for_shipping() -> None:
    status = service.classify_factory_status(
        has_structure=True,
        production_summary={
            "total_pa_orders": 1,
            "total_pi_orders": 0,
            "pa_production_started": "SIM",
            "pi_production_started": "NAO",
        },
        shipping_summary={"total_shipped_quantity": 10, "total_inspection_loss_quantity": 0},
        shipping_items=[{"shipped_quantity": "10"}],
    )

    assert status == "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO"


def test_structure_exclusivity_use_case_returns_summary() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {
        "product_code": "90261255",
        "description": "CHICOTE",
    }
    repository.fetch_structure_with_exclusivity.return_value = [
        {"component_type": "PI"},
        {"component_type": "MP", "exclusive_raw_material": "SIM"},
    ]

    use_case = GetProductStructureExclusivityUseCase(repository)
    result = use_case.execute(ProductPlaybookRequest(code="90261255"))

    assert result["product"]["product_code"] == "90261255"
    assert result["summary"]["total_components"] == 2
    assert result["summary"]["total_exclusive_raw_materials"] == 1


def test_production_status_use_case_uses_reference_date() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {"product_code": "90261255"}
    repository.fetch_production_status.return_value = [
        {
            "level": 0,
            "production_started": "SIM",
            "reported_quantity": "5",
            "production_order": "123",
        }
    ]

    use_case = GetProductProductionStatusUseCase(repository)
    result = use_case.execute(
        ProductPlaybookRequest(code="90261255", reference_date="2026-06-04")
    )

    assert result["reference_date"] == "20260604"
    assert result["summary"]["pa_production_started"] == "SIM"
    repository.fetch_production_status.assert_called_once()


def test_factory_status_use_case_aggregates_sections() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {"product_code": "90261255"}
    repository.fetch_structure_with_exclusivity.return_value = [{"component_type": "MP"}]
    repository.fetch_raw_material_stock.return_value = [
        {
            "raw_material_code": "10010032",
            "available_quantity": "0",
            "has_stock_for_one_pa": "NAO",
        }
    ]
    repository.fetch_production_status.return_value = [
        {
            "level": 0,
            "production_started": "NAO",
            "production_order": "001",
        }
    ]
    repository.fetch_shipping_status.return_value = []

    use_case = GetProductFactoryStatusUseCase(repository)
    result = use_case.execute(ProductPlaybookRequest(code="90261255"))

    assert result["factory_status"] == "OP ABERTA / NÃO INICIADO"
    assert "structure" in result
    assert "raw_material_stock" in result
    assert "production" in result
    assert "shipping" in result
    assert result["indicators"]["total_raw_materials_without_stock_for_one_pa"] == 1


def test_resolve_protheus_date_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        service.resolve_protheus_date("data-invalida")


def test_structure_exclusivity_normalized_types_default() -> None:
    repository = MagicMock()
    repository.fetch_product_header.return_value = {"product_code": "90269001"}
    repository.fetch_structure_with_exclusivity.return_value = [
        {"component_type": "MP", "exclusive_raw_material": "SIM"},
    ]

    use_case = GetProductStructureExclusivityUseCase(repository)
    raw = use_case.execute(ProductPlaybookRequest(code="90269001"))
    result = normalize_playbook_payload(raw, legacy=False)

    assert result["items"][0]["exclusive_raw_material"] is True
    assert result["items"][0]["exclusive_raw_material_label"] == "Sim"
