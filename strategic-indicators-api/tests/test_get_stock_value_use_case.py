from unittest.mock import MagicMock

import pytest

from si_app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from si_app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)


def _build_use_case() -> GetStockValueUseCase:
    repository = MagicMock()
    repository.get_stock_value_summary.return_value = {
        "branch": "consolidated",
        "location": "all",
        "total_stock_value": 100.0,
        "total_stock_quantity": 10.0,
        "total_records": 1,
        "total_products": 1,
        "total_locations": 1,
    }
    repository.get_stock_value_by_branch.return_value = []
    repository.get_stock_value_by_location.return_value = []
    repository.get_top_products_by_stock_value.return_value = []
    return GetStockValueUseCase(repository)


def test_execute_without_dates_does_not_include_estimation():
    use_case = _build_use_case()

    result = use_case.execute(GetStockValueRequest())

    assert "estimation" not in result
    assert result["summary"]["total_stock_value"] == 100.0


def test_execute_with_dates_includes_estimation_metadata():
    use_case = _build_use_case()

    result = use_case.execute(
        GetStockValueRequest(
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    assert result["estimation"]["enabled"] is True
    assert result["estimation"]["start_date"] == "20260401"
    assert result["estimation"]["end_date_exclusive"] == "20260501"


def test_execute_requires_both_dates_for_historical_mode():
    use_case = _build_use_case()

    with pytest.raises(ValueError, match="start_date e end_date"):
        use_case.execute(GetStockValueRequest(start_date="2026-04-01"))


def test_execute_rejects_location_with_historical_mode():
    use_case = _build_use_case()

    with pytest.raises(ValueError, match="localização"):
        use_case.execute(
            GetStockValueRequest(
                start_date="2026-04-01",
                end_date="2026-04-30",
                location="01",
            )
        )
