import pytest

from si_app.application.services.supplies.supplies_metrics_helpers import (
    build_inventory_turnover_payload,
)


def test_build_inventory_turnover_uses_stock_raw_for_stock_context():
    result = build_inventory_turnover_payload(
        branch="02",
        start_date="2026-04-01",
        end_date="2026-04-30",
        location=None,
        turnover_raw={
            "start_date": "20260401",
            "end_date": "20260430",
            "cpv_context": {
                "cpv_total": 2_000_000.0,
                "total_movements": 10,
                "total_quantity": 100.0,
            },
        },
        stock_raw={
            "branch": "02",
            "location": "all",
            "summary": {
                "total_stock_value": 6_554_795.0,
                "total_stock_quantity": 1000.0,
                "total_records": 50,
                "total_products": 40,
                "total_locations": 3,
            },
        },
        strict_idd_period=False,
    )

    assert result["summary"]["total_stock_value"] == 6_554_795.0
    assert result["summary"]["inventory_turnover_months"] == pytest.approx(
        6_554_795.0 / 2_000_000.0
    )
    assert result["stock_estimation"]["enabled"] is True
