import pytest

from si_app.application.services.supplies.supplies_metrics_helpers import (
    build_stock_value_payload,
)


def test_build_stock_value_without_dates_does_not_include_estimation():
    result = build_stock_value_payload(
        branch=None,
        start_date=None,
        end_date=None,
        location=None,
        stock_raw={
            "branch": "consolidated",
            "location": "all",
            "summary": {
                "total_stock_value": 100.0,
                "total_stock_quantity": 10.0,
                "total_records": 1,
                "total_products": 1,
                "total_locations": 1,
            },
            "by_branch": [],
            "by_location": [],
            "top_products": [],
        },
    )

    assert "estimation" not in result
    assert result["summary"]["total_stock_value"] == 100.0


def test_build_stock_value_with_dates_includes_estimation_metadata():
    result = build_stock_value_payload(
        branch=None,
        start_date="2026-04-01",
        end_date="2026-04-30",
        location=None,
        stock_raw={
            "summary": {
                "total_stock_value": 100.0,
                "total_stock_quantity": 10.0,
                "total_records": 1,
                "total_products": 1,
                "total_locations": 1,
            },
        },
    )

    assert result["estimation"]["enabled"] is True
    assert result["estimation"]["start_date"] == "20260401"
    assert result["estimation"]["end_date_exclusive"] == "20260501"


def test_build_stock_value_requires_both_dates_for_historical_mode():
    with pytest.raises(ValueError, match="start_date e end_date"):
        build_stock_value_payload(
            branch=None,
            start_date="2026-04-01",
            end_date=None,
            location=None,
            stock_raw={"summary": {}},
        )


def test_build_stock_value_allows_location_with_historical_mode():
    result = build_stock_value_payload(
        branch=None,
        start_date="2026-04-01",
        end_date="2026-04-30",
        location="01",
        stock_raw={
            "location": "01",
            "summary": {
                "total_stock_value": 100.0,
                "total_stock_quantity": 10.0,
                "total_records": 1,
                "total_products": 1,
                "total_locations": 1,
            },
        },
    )

    assert result["estimation"]["enabled"] is True
