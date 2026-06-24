from unittest.mock import MagicMock

import pytest

from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)


def _build_use_case() -> GetInventoryTurnoverUseCase:
    inventory_repository = MagicMock()
    inventory_repository.get_cpv_context.return_value = {
        "branch": "02",
        "start_date": "20260401",
        "end_date": "20260430",
        "cpv_total": 2_000_000.0,
        "total_movements": 10,
        "total_quantity": 100.0,
    }

    stock_repository = MagicMock()
    stock_repository.get_stock_value_bundle.return_value = {
        "summary": {
            "branch": "02",
            "location": "all",
            "total_stock_value": 6_554_795.0,
            "total_stock_quantity": 1000.0,
            "total_records": 50,
            "total_products": 40,
            "total_locations": 3,
        },
        "stock_method_resolved": "estimated",
        "estimation_meta": {
            "closing_base_date": "20260228",
            "closing_base_value": 6_554_795.0,
            "bridge_value": 0.0,
            "period_net_value": 0.0,
            "official_closure_on_period_end": False,
        },
    }

    return GetInventoryTurnoverUseCase(
        repository=inventory_repository,
        stock_repository=stock_repository,
    )


def test_execute_uses_stock_value_repository_for_stock_context():
    use_case = _build_use_case()

    result = use_case.execute(
        GetInventoryTurnoverRequest(
            branch="02",
            start_date="2026-04-01",
            end_date="2026-04-30",
        )
    )

    stock_repository = use_case._stock_repository
    stock_repository.get_stock_value_bundle.assert_called_once()
    stock_request = stock_repository.get_stock_value_bundle.call_args[0][0]
    assert stock_request.summary_only is True
    assert stock_request.branch == "02"
    assert stock_request.start_date == "2026-04-01"
    assert stock_request.end_date == "2026-04-30"

    assert result["summary"]["total_stock_value"] == 6_554_795.0
    assert result["summary"]["inventory_turnover_months"] == pytest.approx(
        6_554_795.0 / 2_000_000.0
    )
    assert result["stock_estimation"]["enabled"] is True
