from unittest.mock import MagicMock

from app.application.dto.product.exclusive_raw_material_catalog_request import (
    ExclusiveRawMaterialCatalogRequest,
)
from app.application.services.product import product_playbook_service as service
from app.application.use_cases.product.list_exclusive_raw_materials_catalog_use_case import (
    ListExclusiveRawMaterialsCatalogUseCase,
)


def test_group_exclusive_catalog_by_finished_product() -> None:
    rows = [
        {
            "finished_product_code": "90261255",
            "finished_product_description": "CHICOTE",
            "finished_product_unit": "UN",
            "exclusive_raw_material_count": 2,
            "raw_material_code": "10010032",
            "raw_material_description": "CABO",
            "raw_material_unit": "MT",
            "raw_material_group": "1001",
        },
        {
            "finished_product_code": "90261255",
            "finished_product_description": "CHICOTE",
            "finished_product_unit": "UN",
            "exclusive_raw_material_count": 2,
            "raw_material_code": "10070183",
            "raw_material_description": "TERMINAL",
            "raw_material_unit": "UN",
            "raw_material_group": "1007",
        },
    ]

    grouped = service.group_exclusive_catalog_by_finished_product(rows)

    assert len(grouped) == 1
    assert grouped[0]["finished_product_code"] == "90261255"
    assert grouped[0]["exclusive_raw_material_count"] == 2
    assert len(grouped[0]["exclusive_raw_materials"]) == 2


def test_list_exclusive_catalog_by_material_use_case() -> None:
    repository = MagicMock()
    repository.fetch_exclusive_catalog_totals.return_value = {
        "total_exclusive_materials": 1,
        "total_finished_products_with_exclusive": 1,
        "total_exclusive_links": 1,
    }
    repository.fetch_exclusive_catalog_by_material.return_value = [
        {
            "raw_material_code": "10010032",
            "raw_material_description": "CABO",
            "raw_material_unit": "MT",
            "raw_material_group": "1001",
            "finished_product_code": "90261255",
            "finished_product_description": "CHICOTE",
            "finished_product_unit": "UN",
        }
    ]

    use_case = ListExclusiveRawMaterialsCatalogUseCase(repository)
    result = use_case.execute(ExclusiveRawMaterialCatalogRequest(view="by_material", limit=10))

    assert result["view"] == "by_material"
    assert result["items"][0]["exclusive_raw_material"] is True
    assert result["summary"]["total_exclusive_materials"] == 1
    assert result["summary"]["excluded_test_product_prefixes"] == ["8000", "8001"]


def test_list_exclusive_catalog_by_finished_product_use_case() -> None:
    repository = MagicMock()
    repository.fetch_exclusive_catalog_totals.return_value = {
        "total_exclusive_materials": 2,
        "total_finished_products_with_exclusive": 1,
        "total_exclusive_links": 2,
    }
    repository.fetch_exclusive_catalog_by_finished_product.return_value = [
        {
            "finished_product_code": "90261255",
            "finished_product_description": "CHICOTE",
            "finished_product_unit": "UN",
            "exclusive_raw_material_count": 2,
            "raw_material_code": "10010032",
            "raw_material_description": "CABO",
            "raw_material_unit": "MT",
            "raw_material_group": "1001",
        }
    ]

    use_case = ListExclusiveRawMaterialsCatalogUseCase(repository)
    result = use_case.execute(
        ExclusiveRawMaterialCatalogRequest(view="by_finished_product", limit=5)
    )

    assert result["view"] == "by_finished_product"
    assert result["items"][0]["exclusive_raw_material_count"] == 2
    assert result["summary"]["total_finished_products"] == 1
    assert result["summary"]["total_exclusive_links"] == 2
