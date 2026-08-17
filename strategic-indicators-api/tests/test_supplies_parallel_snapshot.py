"""Paralelismo dos fetches core de suprimentos (E2.S1)."""

from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshotService,
)


def test_supplies_build_snapshot_fetches_core_four_ways() -> None:
    supplies = MagicMock()
    financial = MagicMock()
    supplies.fetch_cpv_raw.return_value = {"items": []}
    supplies.fetch_stock_value_raw.return_value = {"items": []}
    supplies.fetch_otd_raw.return_value = {"items": []}
    supplies.fetch_negotiation_savings_summary.return_value = {"branches": []}
    financial.get_rol.return_value = {"rol": 100.0}

    service = SuppliesMetricsSnapshotService(
        supplies_gateway=supplies,
        financial_gateway=financial,
    )
    snapshot = service.get_snapshot(
        start_date="01-06-2026",
        end_date="30-06-2026",
        branch=None,
    )

    assert supplies.fetch_cpv_raw.call_count == 1
    assert financial.get_rol.call_count == 1
    assert supplies.fetch_stock_value_raw.call_count == 1
    assert supplies.fetch_otd_raw.call_count == 1
    assert snapshot.start_date == "01-06-2026"
    assert snapshot.end_date == "30-06-2026"
