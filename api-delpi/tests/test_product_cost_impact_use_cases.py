from unittest.mock import MagicMock

import pytest

from app.application.dto.product.product_cost_impact_request import ProductCostImpactRequest
from app.application.services.product import product_cost_impact_service as service
from app.application.use_cases.product.get_product_cost_impact_simulation_use_case import (
    GetProductCostImpactSimulationUseCase,
)


def test_resolve_unit_cost_prefers_standard_cost() -> None:
    assert (
        service.resolve_unit_cost(
            standard_cost=10,
            last_purchase_price=12,
            price_source="standard_cost",
        )
        == 10.0
    )


def test_resolve_unit_cost_falls_back_to_last_purchase() -> None:
    assert (
        service.resolve_unit_cost(
            standard_cost=0,
            last_purchase_price=12,
            price_source="standard_cost",
        )
        == 12.0
    )


def test_build_cost_impact_simulation_ranks_materials_by_extended_cost() -> None:
    product = {
        "product_code": "90261255",
        "description": "CHICOTE",
        "product_type": "PA",
        "standard_cost": 1000,
    }
    items = [
        {
            "raw_material_code": "10080001",
            "raw_material_description": "MP A",
            "unit": "UN",
            "quantity_per_pa": "10",
            "standard_cost": "5",
            "last_purchase_price": "6",
        },
        {
            "raw_material_code": "10080002",
            "raw_material_description": "MP B",
            "unit": "UN",
            "quantity_per_pa": "2",
            "standard_cost": "100",
            "last_purchase_price": "90",
        },
    ]

    result = service.build_cost_impact_simulation(
        product=product,
        items=items,
        price_source="standard_cost",
        adjustment_percent=10,
        top_n=None,
    )

    materials = result["materials"]["items"]

    assert materials[0]["raw_material_code"] == "10080002"
    assert materials[0]["rank"] == 1
    assert materials[0]["extended_cost"] == 200.0
    assert materials[0]["simulated_extended_cost"] == pytest.approx(220.0)
    assert materials[0]["impact_on_material_cost_percent"] == pytest.approx(80.0)
    assert materials[0]["impact_on_pa_cost_percent"] == pytest.approx(20.0)
    assert result["summary"]["total_material_cost"] == 250.0
    assert result["simulation"]["projected_cost_delta"] == pytest.approx(25.0)


def test_cost_impact_use_case_rejects_non_pa_product() -> None:
    repository = MagicMock()
    repository.fetch_product_cost_header.return_value = {
        "product_code": "10080001",
        "product_type": "MP",
    }

    use_case = GetProductCostImpactSimulationUseCase(repository)

    with pytest.raises(ValueError, match="produto acabado"):
        use_case.execute(ProductCostImpactRequest(code="10080001"))


def test_cost_impact_use_case_returns_ranking() -> None:
    repository = MagicMock()
    repository.fetch_product_cost_header.return_value = {
        "product_code": "90261255",
        "product_type": "PA",
        "standard_cost": 500,
    }
    repository.fetch_raw_material_cost_items.return_value = [
        {
            "raw_material_code": "10080001",
            "raw_material_description": "MP A",
            "unit": "UN",
            "quantity_per_pa": "1",
            "standard_cost": "10",
            "last_purchase_price": "0",
        }
    ]

    use_case = GetProductCostImpactSimulationUseCase(repository)
    result = use_case.execute(ProductCostImpactRequest(code="90261255", top_n=1))

    assert result["product"]["product_code"] == "90261255"
    assert len(result["materials"]["items"]) == 1
    assert result["materials"]["items"][0]["rank"] == 1
