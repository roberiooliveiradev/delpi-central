from __future__ import annotations

from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    COVERAGE_NONE,
    COVERAGE_PARTIAL,
    COVERAGE_SUFFICIENT,
    build_purchase_coverage,
    classify_purchase_coverage,
    enrich_open_purchase_orders,
    remaining_to_buy,
)


def test_classify_coverage_states() -> None:
    assert classify_purchase_coverage(deficit_quantity=100, eligible_open_quantity=0) == (
        COVERAGE_NONE
    )
    assert classify_purchase_coverage(deficit_quantity=100, eligible_open_quantity=40) == (
        COVERAGE_PARTIAL
    )
    assert classify_purchase_coverage(deficit_quantity=100, eligible_open_quantity=100) == (
        COVERAGE_SUFFICIENT
    )


def test_remaining_to_buy_never_negative() -> None:
    assert remaining_to_buy(deficit_quantity=50, eligible_open_quantity=80) == 0.0
    assert remaining_to_buy(deficit_quantity=50, eligible_open_quantity=20) == 30.0


def test_enrich_orders_filters_eligible_warehouses_and_units() -> None:
    orders = [
        {
            "order_number": "000001",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 40,
            "expected_delivery_date": "2026-08-01",
        },
        {
            "order_number": "000002",
            "warehouse": "50",
            "unit": "PC",
            "open_quantity": 100,
            "expected_delivery_date": "2026-07-20",
        },
        {
            "order_number": "000003",
            "warehouse": "99",
            "unit": "KG",
            "open_quantity": 10,
            "expected_delivery_date": "2026-07-15",
        },
    ]
    enriched, totals = enrich_open_purchase_orders(
        orders=orders,
        primary_unit="PC",
        secondary_unit="CX",
        conversion_factor=12,
        conversion_type="M",
    )
    assert totals["eligible_open_quantity"] == 40.0
    assert totals["incompatible_unit_order_count"] == 1
    assert enriched[0]["coverage_eligible"] is True
    assert enriched[1]["coverage_eligible"] is False
    assert enriched[1]["warehouse_eligible"] is False
    assert enriched[2]["unit_compatible"] is False

    coverage = build_purchase_coverage(
        deficit_quantity=100,
        enriched_orders=enriched,
        coverage_totals=totals,
    )
    assert coverage["status"] == COVERAGE_PARTIAL
    assert coverage["remaining_to_buy"] == 60.0
    assert coverage["next_expected_delivery_date"] == "2026-08-01"
