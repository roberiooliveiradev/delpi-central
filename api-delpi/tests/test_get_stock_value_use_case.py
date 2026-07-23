from unittest.mock import MagicMock

import pytest

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)


def _build_use_case() -> GetStockValueUseCase:
    repository = MagicMock()
    repository.get_stock_value_bundle.return_value = {
        "summary": {
            "branch": "consolidated",
            "location": "all",
            "total_stock_value": 100.0,
            "total_stock_quantity": 10.0,
            "total_records": 1,
            "total_products": 1,
            "total_locations": 1,
        },
        "by_branch": [],
        "by_location": [],
        "top_products": [],
    }
    return GetStockValueUseCase(repository)


def test_execute_without_dates_does_not_include_estimation():
    use_case = _build_use_case()

    result = use_case.execute(GetStockValueRequest())

    assert "estimation" not in result
    assert result["summary"]["total_stock_value"] == 100.0


def test_execute_with_dates_includes_estimation_metadata():
    use_case = _build_use_case()
    use_case._repository.get_stock_value_bundle.return_value = {
        "summary": {
            "branch": "consolidated",
            "location": "all",
            "total_stock_value": 100.0,
            "total_stock_quantity": 10.0,
            "total_records": 1,
            "total_products": 1,
            "total_locations": 1,
        },
        "by_branch": [],
        "by_location": [],
        "top_products": [],
        "estimation_meta": {
            "closing_base_date": "20260228",
            "closing_base_value": 200.0,
            "bridge_value": -50.0,
            "period_net_value": -50.0,
            "official_closure_available": True,
            "official_closure_date": "20260228",
            "official_closure_value": 200.0,
            "official_closure_on_period_end": False,
        },
    }

    result = use_case.execute(
        GetStockValueRequest(
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    assert result["estimation"]["enabled"] is True
    assert result["estimation"]["start_date"] == "2026-04-01"
    assert result["estimation"]["end_date"] == "2026-04-30"
    assert result["estimation"]["end_date_exclusive"] == "2026-05-01"
    assert result["estimation"]["closing_base_date"] == "2026-02-28"
    assert result["estimation"]["bridge_value"] == -50.0
    assert result["estimation"]["official_closure_available"] is True
    assert "data_quality_warning" in result["estimation"]


def test_execute_requires_both_dates_for_historical_mode():
    use_case = _build_use_case()

    with pytest.raises(ValueError, match="start_date e end_date"):
        use_case.execute(GetStockValueRequest(start_date="2026-04-01"))


def test_execute_allows_location_with_historical_mode():
    use_case = _build_use_case()

    result = use_case.execute(
        GetStockValueRequest(
            start_date="2026-04-01",
            end_date="2026-04-30",
            location="01",
        )
    )

    assert result["estimation"]["enabled"] is True
