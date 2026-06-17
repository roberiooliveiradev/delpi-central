from app.application.services.product.product_playbook_service import (
    apply_pa_bom_reference_to_stock_items,
    summarize_raw_material_stock,
)
from app.application.services.product.protheus_field_normalizer import (
    normalize_playbook_payload,
)
from app.domain.services.product.product_playbook_numeric_service import (
    ProductPlaybookNumericService,
)


def test_format_quantity_strips_float_artifacts() -> None:
    assert ProductPlaybookNumericService.format_quantity(1575.4399999999996) == "1575.44"
    assert ProductPlaybookNumericService.format_quantity(-504.6750000000011) == "-504.675"
    assert ProductPlaybookNumericService.format_quantity(506.70000000000005) == "506.7"
    assert ProductPlaybookNumericService.format_quantity(4000.0) == "4000"
    assert ProductPlaybookNumericService.format_quantity(2.40925) == "2.4093"


def test_summarize_raw_material_stock_formats_consolidated_quantities() -> None:
    items = apply_pa_bom_reference_to_stock_items(
        [
            {
                "raw_material_code": "10380036",
                "raw_material_description": "CABO AL",
                "unit": "MT",
                "quantity_required_for_one_pa": "230",
                "available_quantity": "787.72",
            },
            {
                "raw_material_code": "10380036",
                "raw_material_description": "CABO AL",
                "unit": "MT",
                "quantity_required_for_one_pa": "230",
                "available_quantity": "787.72",
            },
        ],
        "MI",
    )

    summary = summarize_raw_material_stock(items, product_unit="MI")
    material = summary["materials"][0]

    assert material["available_quantity"] == "1575.44"
    assert material["pa_producible_from_stock"] == "6.8497"


def test_normalize_playbook_payload_formats_stock_summary_materials() -> None:
    payload = {
        "raw_material_stock": {
            "summary": {
                "materials": [
                    {
                        "raw_material_code": "10380040",
                        "available_quantity": 506.70000000000005,
                        "pa_producible_from_stock": 2.2030000000000003,
                    }
                ]
            },
            "items": [
                {
                    "raw_material_code": "10380040",
                    "available_quantity": 506.70000000000005,
                    "has_stock_for_one_pa": "NAO",
                }
            ],
        }
    }

    normalized = normalize_playbook_payload(payload, legacy=False)

    material = normalized["raw_material_stock"]["summary"]["materials"][0]
    item = normalized["raw_material_stock"]["items"][0]

    assert material["available_quantity"] == "506.7"
    assert material["pa_producible_from_stock"] == "2.203"
    assert item["available_quantity"] == "506.7"
