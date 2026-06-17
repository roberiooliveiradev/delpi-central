from app.application.services.product.product_playbook_service import (
    apply_pa_bom_reference_to_stock_items,
    summarize_raw_material_stock,
)


def test_apply_pa_bom_reference_recalculates_has_stock_for_one_pa() -> None:
    items = apply_pa_bom_reference_to_stock_items(
        [
            {
                "raw_material_code": "10080063",
                "quantity_required_for_one_pa": "30",
                "available_quantity": "25",
                "has_stock_for_one_pa": "SIM",
            },
            {
                "raw_material_code": "10080063",
                "quantity_required_for_one_pa": "30",
                "available_quantity": "10",
                "has_stock_for_one_pa": "SIM",
            },
        ],
        "MI",
    )

    summary = summarize_raw_material_stock(items, product_unit="MI")

    assert summary["total_without_stock_for_one_pa"] == 0
    assert summary["max_pa_producible_from_stock"] == "1"
    assert summary["limiting_raw_material_code"] == "10080063"
    assert items[0]["has_stock_for_one_pa"] == "NAO"
    assert items[1]["has_stock_for_one_pa"] == "NAO"


def test_summarize_raw_material_stock_reports_zero_pa_when_bottleneck_has_no_stock() -> None:
    items = apply_pa_bom_reference_to_stock_items(
        [
            {
                "raw_material_code": "10080063",
                "quantity_required_for_one_pa": "30",
                "available_quantity": "0",
                "has_stock_for_one_pa": "NAO",
            },
            {
                "raw_material_code": "10160002",
                "quantity_required_for_one_pa": "10",
                "available_quantity": "1000",
                "has_stock_for_one_pa": "SIM",
            },
        ],
        "MI",
    )

    summary = summarize_raw_material_stock(items, product_unit="MI")

    assert summary["max_pa_producible_from_stock"] == "0"
    assert summary["limiting_raw_material_code"] == "10080063"
