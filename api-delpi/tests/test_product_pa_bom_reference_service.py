from app.domain.services.product.product_pa_bom_reference_service import (
    ProductPaBomReferenceService,
)


def test_resolve_mi_keeps_one_pa_reference() -> None:
    reference = ProductPaBomReferenceService.resolve("MI")

    assert reference.reference_quantity == 1
    assert reference.reference_unit == "PA"
    assert reference.catalog_unit == "MI"
    assert reference.bom_quantity_factor == 1


def test_quantity_required_for_one_pa_uses_identity_for_mi() -> None:
    assert ProductPaBomReferenceService.quantity_required_for_one_pa("30", "MI") == 30.0


def test_has_stock_for_one_pa_compares_available_to_required() -> None:
    assert (
        ProductPaBomReferenceService.has_stock_for_one_pa(
            available_quantity="29",
            required_quantity=30,
        )
        == "NAO"
    )
    assert (
        ProductPaBomReferenceService.has_stock_for_one_pa(
            available_quantity="30",
            required_quantity=30,
        )
        == "SIM"
    )


def test_pa_producible_from_stock_divides_available_by_required() -> None:
    assert ProductPaBomReferenceService.pa_producible_from_stock(
        available_quantity="351000",
        required_quantity="3000",
    ) == 117.0


def test_summarize_pa_producible_capacity_uses_bottleneck_material() -> None:
    capacity = ProductPaBomReferenceService.summarize_pa_producible_capacity(
        [
            {
                "raw_material_code": "10080063",
                "raw_material_description": "TERM FASTON",
                "quantity_required_for_one_pa": "3000",
                "available_quantity": "351000",
            },
            {
                "raw_material_code": "10160002",
                "raw_material_description": "RESISTOR",
                "quantity_required_for_one_pa": "30",
                "available_quantity": "25",
            },
        ]
    )

    assert capacity["max_pa_producible_from_stock"] == "0"
    assert capacity["limiting_raw_material_code"] == "10160002"
    assert capacity["materials"][0]["pa_producible_from_stock"] == "117.0"
    assert capacity["materials"][1]["pa_producible_from_stock"] == "0.8333"
