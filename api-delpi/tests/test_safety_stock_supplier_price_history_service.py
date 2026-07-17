from __future__ import annotations

from app.domain.services.supplies.safety_stock_supplier_price_history_service import (
    map_supplier_price_history_items,
    summarize_supplier_price_history,
)


def test_map_supplier_price_history_items_orders_chronologically() -> None:
    mapped = map_supplier_price_history_items(
        [
            {
                "branch": "01",
                "entry_date": "20260710",
                "issue_date": "20260709",
                "supplier_code": "F001",
                "supplier_store": "01",
                "supplier_name": "ACME",
                "unit_price": 12.5,
                "quantity": 10,
                "total_value": 125,
                "invoice_number": "002",
                "invoice_series": "1",
            },
            {
                "branch": "01",
                "entry_date": "20260115",
                "issue_date": "20260114",
                "supplier_code": "F001",
                "supplier_store": "01",
                "supplier_name": "ACME",
                "unit_price": 10.0,
                "quantity": 5,
                "total_value": 50,
                "invoice_number": "001",
                "invoice_series": "1",
            },
        ]
    )

    assert [item["purchase_date"] for item in mapped] == ["2026-01-15", "2026-07-10"]
    assert mapped[0]["unit_price"] == 10.0
    assert mapped[1]["invoice_number"] == "002"


def test_summarize_supplier_price_history_variation() -> None:
    summary = summarize_supplier_price_history(
        [
            {"unit_price": 10.0},
            {"unit_price": 12.5},
        ]
    )

    assert summary["total_purchases"] == 2
    assert summary["min_unit_price"] == 10.0
    assert summary["max_unit_price"] == 12.5
    assert summary["first_unit_price"] == 10.0
    assert summary["last_unit_price"] == 12.5
    assert summary["variation_percent"] == 25.0


def test_summarize_supplier_price_history_empty() -> None:
    summary = summarize_supplier_price_history([])
    assert summary["total_purchases"] == 0
    assert summary["variation_percent"] is None
