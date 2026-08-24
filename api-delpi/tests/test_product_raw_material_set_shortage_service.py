from __future__ import annotations

from app.domain.services.product.product_raw_material_set_shortage_service import (
    STATUS_NO_COMMITMENT,
    STATUS_OK,
    STATUS_SHORTAGE,
    build_raw_material_set_shortages,
)


def _material(**overrides: object) -> dict:
    base = {
        "product_code": "10080001",
        "product_description": "CABO",
        "unit": "KG",
        "secondary_unit": "",
        "conversion_factor": None,
        "conversion_type": "",
        "available_stock": 10.0,
        "safety_stock": 5.0,
        "structure_quantity": 1.0,
        "bom_level": 1,
    }
    base.update(overrides)
    return base


def _order(**overrides: object) -> dict:
    base = {
        "branch": "01",
        "production_order": "24608101001",
        "order_number": "246081",
        "order_item": "01",
        "product_code": "90263114",
        "product_description": "CHICOTE",
        "planned_start_date": "2026-09-12",
        "due_date": "2026-09-20",
        "planned_quantity": 10.0,
        "produced_quantity": 0.0,
        "open_quantity": 10.0,
        "observation": "",
    }
    base.update(overrides)
    return base


def _commitment(**overrides: object) -> dict:
    base = {
        "warehouse": "01",
        "unit": "KG",
        "open_quantity": 12.0,
        "commitment_date": "2026-09-12",
        "production_order": "24608101003",
        "finished_production_order": "24608101001",
        "finished_product_code": "90263114",
        "product_code": "10080001",
    }
    base.update(overrides)
    return base


def test_marks_shortage_only_for_the_set_that_goes_negative() -> None:
    payload = build_raw_material_set_shortages(
        product={"product_code": "90263114", "product_type": "PA"},
        materials=[_material(available_stock=10.0)],
        mother_orders=[
            _order(),
            _order(
                production_order="24609001001",
                order_number="246090",
                planned_start_date="2026-09-28",
            ),
        ],
        purchase_orders=[
            {
                "product_code": "10080001",
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 20.0,
                "expected_delivery_date": "2026-09-20",
                "order_number": "PC1",
                "order_item": "01",
                "supplier_name": "Fornecedor",
            }
        ],
        commitments=[
            _commitment(),
            _commitment(
                production_order="24609001003",
                finished_production_order="24609001001",
                commitment_date="2026-09-28",
                open_quantity=1.0,
            ),
        ],
    )

    statuses = {item["production_order"]: item["status"] for item in payload["sets"]}
    assert statuses["24608101001"] == STATUS_SHORTAGE
    assert statuses["24609001001"] == STATUS_OK
    first = next(
        item for item in payload["sets"] if item["production_order"] == "24608101001"
    )
    mp = first["materials"][0]
    assert mp["status"] == STATUS_SHORTAGE
    assert mp["shortage_date"] == "2026-09-12"
    assert mp["shortage_quantity"] == 2.0
    assert mp["needed_quantity"] == 12.0
    assert mp["consuming_production_order"] == "24608101003"
    assert payload["summary"]["at_risk_set_count"] == 1
    assert payload["summary"]["short_mp_count"] == 1
    assert payload["summary"]["first_shortage_date"] == "2026-09-12"


def test_does_not_mix_sets_when_item_is_not_01() -> None:
    payload = build_raw_material_set_shortages(
        product={"product_code": "90263114", "product_type": "PA"},
        materials=[_material(available_stock=0.0)],
        mother_orders=[
            _order(production_order="24608102001", order_item="02"),
        ],
        purchase_orders=[],
        commitments=[
            _commitment(
                production_order="24608101003",
                finished_production_order="24608101001",
                finished_product_code="90269999",
            )
        ],
    )

    assert payload["sets"][0]["status"] == STATUS_NO_COMMITMENT
    assert payload["sets"][0]["materials"][0]["status"] == STATUS_NO_COMMITMENT


def test_other_pa_on_same_extract_does_not_flag_this_set() -> None:
    payload = build_raw_material_set_shortages(
        product={"product_code": "90263114", "product_type": "PA"},
        materials=[_material(available_stock=5.0)],
        mother_orders=[_order()],
        purchase_orders=[],
        commitments=[
            _commitment(
                finished_production_order="11111101001",
                finished_product_code="90260000",
                production_order="11111101003",
                open_quantity=20.0,
                commitment_date="2026-09-10",
            ),
            _commitment(open_quantity=1.0, commitment_date="2026-09-12"),
        ],
    )

    # O empenho do outro PA já deixou o saldo negativo; o deste conjunto
    # ainda é shortage (o extrato é global). O que não pode acontecer é
    # atribuir o empenho do outro PA como consuming_production_order.
    first = payload["sets"][0]
    assert first["status"] == STATUS_SHORTAGE
    assert first["materials"][0]["consuming_production_order"] == "24608101003"


def test_set_without_commitment_stays_no_commitment() -> None:
    payload = build_raw_material_set_shortages(
        product={"product_code": "90263114", "product_type": "PA"},
        materials=[_material()],
        mother_orders=[_order()],
        purchase_orders=[],
        commitments=[],
    )
    assert payload["sets"][0]["status"] == STATUS_NO_COMMITMENT
    assert payload["summary"]["no_commitment_set_count"] == 1
