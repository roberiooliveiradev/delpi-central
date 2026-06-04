from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshot,
)
from si_app.infrastructure.providers.strategic_indicators.supplies_indicators_snapshot_provider import (
    SuppliesIndicatorsSnapshotProvider,
)


def _snapshot(**overrides) -> SuppliesMetricsSnapshot:
    defaults = {
        "branch": None,
        "start_date": "2026-05-01",
        "end_date": "2026-05-31",
        "cpv_pct": 0.0,
        "inventory_turnover_months": 0.0,
        "otd_pct": 0.0,
        "stock_value": 0.0,
        "negotiation_savings_by_branch": {"01": 15000.0, "02": 22000.0},
    }
    defaults.update(overrides)
    return SuppliesMetricsSnapshot(**defaults)


def test_supplies_snapshot_exposes_negotiation_savings_with_unit_values() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = _snapshot()

    provider = SuppliesIndicatorsSnapshotProvider(
        supplies_metrics_snapshot_service=service,
    )
    result = provider.get_supplies_indicators_snapshot(
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    negotiation = next(
        item
        for item in result["items"]
        if item["indicator_id"] == "supplies-negotiation-savings"
    )

    assert negotiation["source"] == "supplies_negotiation_savings"
    assert negotiation["value"] == 37000.0
    assert negotiation["unit_values"]["01"] == 15000.0
    assert negotiation["unit_values"]["02"] == 22000.0


def test_supplies_snapshot_negotiation_savings_null_when_no_branch_data() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = _snapshot(
        negotiation_savings_by_branch={"01": None, "02": None},
    )

    provider = SuppliesIndicatorsSnapshotProvider(
        supplies_metrics_snapshot_service=service,
    )
    result = provider.get_supplies_indicators_snapshot(
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    negotiation = next(
        item
        for item in result["items"]
        if item["indicator_id"] == "supplies-negotiation-savings"
    )

    assert negotiation["value"] is None
    assert negotiation["unit_values"]["01"] is None
    assert negotiation["unit_values"]["02"] is None


def test_supplies_metrics_snapshot_loads_negotiation_savings_from_gateway() -> None:
    from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
        SuppliesMetricsSnapshotService,
    )

    negotiation_use_case = MagicMock()
    negotiation_use_case.execute.return_value = {
        "branches": [
            {"branch": "01", "total_savings": 15000.0},
            {"branch": "02", "total_savings": 22000.0},
        ],
    }

    cpv_use_case = MagicMock()
    cpv_use_case.execute.return_value = {"data": {"summary": {"cpv_percentage": 0}}}

    inventory_use_case = MagicMock()
    inventory_use_case.execute.return_value = {
        "data": {"summary": {"inventory_turnover_months": 0}},
    }

    otd_use_case = MagicMock()
    otd_use_case.execute.return_value = {"data": {"summary": {"otd_percentage": 0}}}

    stock_use_case = MagicMock()
    stock_use_case.execute.return_value = {"data": {"summary": {"total_stock_value": 0}}}

    service = SuppliesMetricsSnapshotService(
        get_cpv_use_case=cpv_use_case,
        get_inventory_turnover_use_case=inventory_use_case,
        get_otd_use_case=otd_use_case,
        get_stock_value_use_case=stock_use_case,
        get_negotiation_savings_summary_use_case=negotiation_use_case,
    )

    snapshot = service.get_snapshot(
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    assert snapshot.negotiation_savings_by_branch == {"01": 15000.0, "02": 22000.0}
    negotiation_use_case.execute.assert_called_once()
