"""GLPI #635: weighted cross-branch conversion averages, no fabricated zero."""

from unittest.mock import MagicMock

from si_app.application.services.supplies.supplies_metrics_snapshot_service import (
    SuppliesMetricsSnapshot, SuppliesMetricsSnapshotService,
)
from si_app.infrastructure.providers.strategic_indicators.supplies_indicators_snapshot_provider import (
    SuppliesIndicatorsSnapshotProvider,
)


def _snapshot(**overrides):
    args = {
        "branch": None,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "cpv_pct": 0,
        "inventory_turnover_times": 0,
        "otd_pct": 0,
        "stock_value": 0,
        "sc_pc_conversion_by_branch": {
            "01": {"converted_requests": 10, "sum_conversion_days": 30},
            "02": {"converted_requests": 2, "sum_conversion_days": 20},
        },
    }
    args.update(overrides)
    return SuppliesMetricsSnapshot(**args)


def _measure(snapshot):
    provider = SuppliesIndicatorsSnapshotProvider(
        supplies_metrics_snapshot_service=MagicMock(),
    )
    result = provider._map_snapshot_to_result(snapshot=snapshot)
    return next(
        row for row in result["items"]
        if row["indicator_id"] == "supplies-sc-pc-conversion-days"
    )


def test_consolidated_is_weighted_by_converted_sc_not_mean_of_branches():
    measurement = _measure(_snapshot())
    assert measurement["value"] == 4.17  # 50 / 12, not (3+10)/2=6.5
    assert measurement["unit_values"]["01"] == 3.0
    assert measurement["unit_values"]["02"] == 10.0
    assert measurement["unit_values"]["consolidated"] == 4.17
    assert measurement["source"] == "supplies_sc_pc_conversion"


def test_unavailable_branch_blocks_consolidated_and_no_conversions_yield_null():
    missing = _measure(_snapshot(sc_pc_conversion_by_branch={
        "01": {"converted_requests": 10, "sum_conversion_days": 30},
        "02": None,
    }))
    assert missing["value"] is None
    assert missing["unit_values"]["02"] is None
    no_conversions = _measure(_snapshot(sc_pc_conversion_by_branch={
        "01": {"converted_requests": 0, "sum_conversion_days": 0},
        "02": {"converted_requests": 0, "sum_conversion_days": 0},
    }))
    assert no_conversions["value"] is None


def test_single_branch_isolated_and_zero_is_not_fabricated():
    single = _measure(_snapshot(
        branch="01",
        sc_pc_conversion_by_branch={
            "01": {"converted_requests": 10, "sum_conversion_days": 30},
        },
    ))
    assert single["value"] == 3.0
    assert single["unit_values"]["02"] is None

    source = SuppliesMetricsSnapshotService(
        supplies_gateway=MagicMock(), financial_gateway=MagicMock(),
    )
    source._supplies_gateway.fetch_sc_pc_conversion_summary.return_value = {
        "source": "SC1010+SCR010+SC7010",
        "scope": "release_or_issue_without_approval_to_first_order",
        "branch_breakdown": {
            "01": {"sum_conversion_days": 30, "converted_requests": 10},
            "02": {"sum_conversion_days": 20, "converted_requests": 2},
        },
    }
    assert source._load_sc_pc_conversion(
        branch=None, start_date="2026-10-01", end_date="2026-10-31",
    ) == {
        "01": {"sum_conversion_days": 30, "converted_requests": 10},
        "02": {"sum_conversion_days": 20, "converted_requests": 2},
    }
    source._supplies_gateway.fetch_sc_pc_conversion_summary.side_effect = RuntimeError("down")
    assert source._load_sc_pc_conversion(
        branch=None, start_date="2026-10-01", end_date="2026-10-31",
    ) == {"01": None, "02": None}
