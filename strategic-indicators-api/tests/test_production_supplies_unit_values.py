from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.production.production_metrics_snapshot_service import (
    ProductionUnitMetricsSnapshot,
)
from si_app.infrastructure.providers.strategic_indicators.production_indicators_snapshot_provider import (
    ProductionIndicatorsSnapshotProvider,
)


def test_production_consolidated_measurement_includes_branch_unit_values() -> None:
    service = MagicMock()
    consolidated = ProductionUnitMetricsSnapshot(
        branch=None,
        start_date="01-04-2026",
        end_date="30-04-2026",
        rol=100.0,
        average_direct_labor_cost=10.0,
        average_production_cost=0.0,
        average_depreciation_cost=0.0,
        direct_labor_cost_pct=4.68,
        production_cost_pct=None,
        depreciation_pct=None,
        oee_pct=None,
        otd_pct=None,
    )
    unit_01 = ProductionUnitMetricsSnapshot(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
        rol=50.0,
        average_direct_labor_cost=5.0,
        average_production_cost=0.0,
        average_depreciation_cost=0.0,
        direct_labor_cost_pct=5.0,
        production_cost_pct=None,
        depreciation_pct=None,
        oee_pct=None,
        otd_pct=None,
    )
    unit_02 = ProductionUnitMetricsSnapshot(
        branch="02",
        start_date="01-04-2026",
        end_date="30-04-2026",
        rol=50.0,
        average_direct_labor_cost=4.0,
        average_production_cost=0.0,
        average_depreciation_cost=0.0,
        direct_labor_cost_pct=4.0,
        production_cost_pct=None,
        depreciation_pct=None,
        oee_pct=None,
        otd_pct=None,
    )

    service.get_consolidated_snapshot.return_value = consolidated
    service.get_unit_snapshot.side_effect = lambda *, branch, **kwargs: (
        unit_01 if branch == "01" else unit_02
    )

    provider = ProductionIndicatorsSnapshotProvider(
        production_metrics_snapshot_service=service,
    )
    result = provider.get_production_indicators_snapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )

    direct_labor = next(
        item for item in result["items"] if item["indicator_id"] == "production-direct-labor"
    )
    assert direct_labor["value"] == 4.68
    assert direct_labor["unit_values"]["consolidated"] == 4.68
    assert direct_labor["unit_values"]["01"] == 5.0
    assert direct_labor["unit_values"]["02"] == 4.0
