from app.domain.services.production.production_operational_quantity_service import (
    ProductionOperationalQuantityService,
)


def test_resolve_mi_converts_to_display_units() -> None:
    profile = ProductionOperationalQuantityService.resolve("MI")

    assert profile.catalog_unit == "MI"
    assert profile.display_unit_factor == 1000
    assert profile.display_unit == "UN"
    assert profile.converts_catalog_unit() is True


def test_convert_mi_planned_qty_to_pieces() -> None:
    assert ProductionOperationalQuantityService.convert_quantity(0.003, "MI") == 3.0
    assert ProductionOperationalQuantityService.convert_quantity(5, "MI") == 5000.0


def test_normalize_item_converts_mi_fields_and_unit() -> None:
    normalized = ProductionOperationalQuantityService.normalize_item(
        {
            "production_order": "24602201014",
            "planned_qty": 0.003,
            "unit": "MI",
        }
    )

    assert normalized["planned_qty"] == 3.0
    assert normalized["unit"] == "UN"
    assert normalized["production_order"] == "24602201014"


def test_normalize_item_keeps_non_mi_units() -> None:
    item = {"planned_qty": 10, "unit": "KG"}
    assert ProductionOperationalQuantityService.normalize_item(item) == item


def test_normalize_item_converts_open_order_quantities() -> None:
    normalized = ProductionOperationalQuantityService.normalize_item(
        {
            "planned_qty": 0.003,
            "produced_qty": 0.002,
            "pending_qty": 0.001,
            "unit": "MI",
        }
    )

    assert normalized["planned_qty"] == 3.0
    assert normalized["produced_qty"] == 2.0
    assert normalized["pending_qty"] == 1.0
    assert normalized["unit"] == "UN"


def test_normalize_items_preserves_order() -> None:
    items = ProductionOperationalQuantityService.normalize_items(
        [
            {"planned_qty": 0.003, "unit": "MI"},
            {"planned_qty": 12, "unit": "PC"},
        ]
    )

    assert items[0]["planned_qty"] == 3.0
    assert items[1]["planned_qty"] == 12


def test_normalize_appointment_qty_fields_mi_to_un() -> None:
    normalized = ProductionOperationalQuantityService.normalize_item(
        {
            "qty_produced": 3.836,
            "qty_lost": 0.01,
            "unit": "MI",
        }
    )

    assert normalized["qty_produced"] == 3836.0
    assert normalized["qty_lost"] == 10.0
    assert normalized["unit"] == "UN"
