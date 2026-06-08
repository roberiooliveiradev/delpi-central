from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialBranchSnapshot,
    FinancialMetricsSnapshot,
)
from si_app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)
from si_app.shared.branch_filter import FINANCIAL_CONSOLIDATED_BRANCH_KEY


def test_financial_provider_maps_missing_ebitda_and_fixed_cost_as_null() -> None:
    snapshot = FinancialMetricsSnapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branches=[
            FinancialBranchSnapshot(
                branch=FINANCIAL_CONSOLIDATED_BRANCH_KEY,
                rol=1_000_000.0,
                ebitda_value=None,
                fixed_cost_value=None,
                pmr_days=None,
                ebitda_over_rol_pct=None,
                fixed_cost_over_rol_pct=None,
            ),
        ],
    )
    service = MagicMock()
    service.get_snapshot.return_value = snapshot
    provider = FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=service,
    )

    result = provider.get_financial_indicators_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    values = {item["indicator_id"]: item["value"] for item in result["items"]}
    assert values["financial-ebitda"] is None
    assert values["financial-fixed-cost"] is None
    assert values["financial-pmr"] is None
