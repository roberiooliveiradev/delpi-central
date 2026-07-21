from __future__ import annotations

from datetime import date

from app.domain.services.supplies.safety_stock_stock_projection_service import (
    PROJECTION_DEFICIT,
    PROJECTION_SUFFICIENT,
    PROJECTION_TEMPORARY_SHORTAGE,
    build_stock_projection,
    enrich_open_commitments,
    finished_production_order_from_component_op,
    format_commitment_ledger_reference,
)


def test_finished_production_order_from_component_op() -> None:
    assert finished_production_order_from_component_op("24608101003") == "24608101001"
    assert finished_production_order_from_component_op("24607701001") == "24607701001"
    assert finished_production_order_from_component_op("123") is None


def test_format_commitment_ledger_reference_keeps_only_op() -> None:
    assert (
        format_commitment_ledger_reference(
            production_order="24608101003",
            finished_product_code="90261255",
        )
        == "24608101003"
    )
    assert format_commitment_ledger_reference(production_order="24608101003") == (
        "24608101003"
    )
    assert format_commitment_ledger_reference(production_order="") == "Empenho"


def test_enrich_commitments_converts_and_marks_ineligible_warehouse() -> None:
    enriched, totals = enrich_open_commitments(
        commitments=[
            {
                "warehouse": "01",
                "unit": "PC",
                "open_quantity": 10.0,
                "commitment_date": "20260720",
                "production_order": "OP1",
            },
            {
                "warehouse": "50",
                "unit": "PC",
                "open_quantity": 5.0,
                "commitment_date": "20260721",
                "production_order": "OP2",
            },
            {
                "warehouse": "01",
                "unit": "CX",
                "open_quantity": 2.0,
                "commitment_date": "20260722",
                "production_order": "OP3",
            },
        ],
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12.0,
        conversion_type="M",
    )

    assert enriched[0]["projection_eligible"] is True
    assert enriched[0]["open_quantity_primary_unit"] == 10.0
    assert enriched[1]["warehouse_eligible"] is False
    assert enriched[1]["projection_eligible"] is False
    assert enriched[2]["unit_compatible"] is True
    assert enriched[2]["open_quantity_primary_unit"] == 2.0 / 12.0
    assert totals["eligible_open_quantity"] == 10.0 + (2.0 / 12.0)


def test_projection_detects_temporary_shortage_before_purchase_arrives() -> None:
    """Saldo 100, empenho -150 em 20/07, compra +200 em 30/07 → falta temporária."""
    as_of = date(2026, 7, 16)
    orders = [
        {
            "order_number": "PC200",
            "order_item": "01",
            "warehouse": "01",
            "expected_delivery_date": "2026-07-30",
            "open_quantity_primary_unit": 200.0,
            "coverage_eligible": True,
            "unit_compatible": True,
            "supplier_name": "TRAMAR",
        }
    ]
    commitments = [
        {
            "production_order": "OP150",
            "warehouse": "01",
            "commitment_date": "2026-07-20",
            "open_quantity_primary_unit": 150.0,
            "projection_eligible": True,
            "unit_compatible": True,
        }
    ]

    result = build_stock_projection(
        available_stock=100.0,
        safety_stock=0.0,
        enriched_orders=orders,
        enriched_commitments=commitments,
        as_of_date=as_of,
    )
    summary = result["summary"]
    balances = [row["running_balance"] for row in result["items"]]

    assert balances[0] == 100.0
    assert min(balances) == -50.0
    assert summary["final_projected_balance"] == 150.0
    assert summary["minimum_projected_balance"] == -50.0
    assert summary["first_shortage_date"] == "2026-07-20"
    assert result["items"][0]["inflow"] == 0.0
    assert result["items"][0]["outflow"] == 0.0
    assert summary["status"] == PROJECTION_SUFFICIENT  # sem ESTSEG
    assert result["items"][1]["origin"] == "commitment"
    assert result["items"][1]["outflow"] == 150.0
    assert result["items"][2]["origin"] == "purchase_order"
    assert result["items"][2]["reference"] == "PC200/01 - TRAMAR"


def test_projection_marks_temporary_shortage_against_safety_stock() -> None:
    as_of = date(2026, 7, 16)
    result = build_stock_projection(
        available_stock=100.0,
        safety_stock=80.0,
        enriched_orders=[
            {
                "order_number": "PC200",
                "order_item": "01",
                "warehouse": "01",
                "expected_delivery_date": "2026-07-30",
                "open_quantity_primary_unit": 200.0,
                "coverage_eligible": True,
                "unit_compatible": True,
            }
        ],
        enriched_commitments=[
            {
                "production_order": "OP150",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 150.0,
                "projection_eligible": True,
                "unit_compatible": True,
            }
        ],
        as_of_date=as_of,
    )
    summary = result["summary"]
    assert summary["status"] == PROJECTION_TEMPORARY_SHORTAGE
    assert summary["first_shortage_date"] == "2026-07-20"
    assert summary["final_projected_balance"] == 150.0
    assert summary["projected_remaining_to_buy"] == 0.0


def test_projection_commitment_includes_finished_product_on_ledger() -> None:
    as_of = date(2026, 7, 16)
    result = build_stock_projection(
        available_stock=100.0,
        safety_stock=80.0,
        enriched_orders=[],
        enriched_commitments=[
            {
                "production_order": "24608101003",
                "finished_production_order": "24608101001",
                "finished_product_code": "90261255",
                "finished_order_observation": "PED CLIENTE XYZ",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 10.0,
                "projection_eligible": True,
                "unit_compatible": True,
            }
        ],
        as_of_date=as_of,
    )
    commitment_rows = [
        row for row in result["items"] if row["origin"] == "commitment"
    ]
    assert len(commitment_rows) == 1
    assert commitment_rows[0]["reference"] == "24608101003"
    assert commitment_rows[0]["finished_production_order"] == "24608101001"
    assert commitment_rows[0]["finished_product_code"] == "90261255"
    assert commitment_rows[0]["finished_order_observation"] == "PED CLIENTE XYZ"


def test_projection_same_day_applies_outflows_before_inflows() -> None:
    as_of = date(2026, 7, 16)
    result = build_stock_projection(
        available_stock=100.0,
        safety_stock=0.0,
        enriched_orders=[
            {
                "order_number": "PC1",
                "order_item": "01",
                "warehouse": "01",
                "expected_delivery_date": "2026-07-20",
                "open_quantity_primary_unit": 50.0,
                "coverage_eligible": True,
                "unit_compatible": True,
            }
        ],
        enriched_commitments=[
            {
                "production_order": "OP1",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 80.0,
                "projection_eligible": True,
                "unit_compatible": True,
            }
        ],
        as_of_date=as_of,
    )
    day_rows = [row for row in result["items"] if row["event_date"] == "2026-07-20"]
    assert day_rows[0]["origin"] == "commitment"
    assert day_rows[0]["running_balance"] == 20.0
    assert day_rows[1]["origin"] == "purchase_order"
    assert day_rows[1]["running_balance"] == 70.0


def test_projection_deficit_when_final_below_safety() -> None:
    as_of = date(2026, 7, 16)
    result = build_stock_projection(
        available_stock=40.0,
        safety_stock=100.0,
        enriched_orders=[],
        enriched_commitments=[
            {
                "production_order": "OP1",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 10.0,
                "projection_eligible": True,
                "unit_compatible": True,
            }
        ],
        as_of_date=as_of,
    )
    summary = result["summary"]
    assert summary["status"] == PROJECTION_DEFICIT
    assert summary["final_projected_balance"] == 30.0
    assert summary["projected_remaining_to_buy"] == 70.0
    assert summary["final_balance_after_safety"] == -70.0
    # Saldo nunca fica negativo: ruptura só quando o saldo projetado é < 0.
    assert summary["first_shortage_date"] is None


def test_incompatible_commitment_excluded_from_projection_but_listed() -> None:
    enriched, totals = enrich_open_commitments(
        commitments=[
            {
                "warehouse": "01",
                "unit": "KG",
                "open_quantity": 5.0,
                "commitment_date": "2026-07-20",
                "production_order": "OPX",
            }
        ],
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12.0,
        conversion_type="M",
    )
    assert enriched[0]["projection_eligible"] is False
    assert totals["eligible_open_quantity"] == 0.0
    assert totals["incompatible_unit_commitment_count"] == 1

    result = build_stock_projection(
        available_stock=100.0,
        safety_stock=0.0,
        enriched_orders=[],
        enriched_commitments=enriched,
        commitment_totals=totals,
        as_of_date=date(2026, 7, 16),
    )
    assert len(result["items"]) == 1
    assert result["items"][0]["origin"] == "initial_balance"
