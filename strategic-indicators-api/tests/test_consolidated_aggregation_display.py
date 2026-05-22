from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.commercial.commercial_metrics_snapshot_service import (
    CommercialMetricsSnapshot,
)
from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialBranchSnapshot,
    FinancialMetricsSnapshot,
)
from si_app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.infrastructure.providers.strategic_indicators.commercial_indicators_snapshot_provider import (
    CommercialIndicatorsSnapshotProvider,
)
from si_app.infrastructure.providers.strategic_indicators.financial_indicators_snapshot_provider import (
    FinancialIndicatorsSnapshotProvider,
)
from si_app.shared.branch_filter import build_unit_values_for_consolidated_department


def test_build_unit_values_consolidated_only() -> None:
    assert build_unit_values_for_consolidated_department(
        consolidated_value=10.0,
        view_branch="02",
    ) == {"consolidated": 10.0}


def test_build_realized_payload_for_consolidated_departments() -> None:
    calculator = StrategicIndicatorsCalculator()
    raw = {"consolidated": 50.0, "02": 50.0}

    for department_id in ("engineering", "financial", "commercial"):
        assert calculator.build_realized_payload(
            unit_values=raw,
            value=50.0,
            department_id=department_id,
        ) == {"consolidated": 50.0}


def test_financial_provider_exposes_consolidated_unit_values_on_branch_view() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = FinancialMetricsSnapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branches=[
            FinancialBranchSnapshot(
                branch=CONSOLIDATED_BRANCH_KEY,
                rol_with_ipi=1_000_000.0,
                ebitda_value=125_000.0,
                fixed_cost_value=80_000.0,
                pmr_days=45.0,
                ebitda_over_rol_pct=12.5,
                fixed_cost_over_rol_pct=8.0,
            ),
            FinancialBranchSnapshot(
                branch="01",
                rol_with_ipi=500_000.0,
                ebitda_value=55_000.0,
                fixed_cost_value=35_000.0,
                pmr_days=40.0,
                ebitda_over_rol_pct=11.0,
                fixed_cost_over_rol_pct=7.0,
            ),
        ],
    )

    provider = FinancialIndicatorsSnapshotProvider(
        financial_metrics_snapshot_service=service,
    )
    result = provider.get_financial_indicators_snapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch="02",
    )

    ebitda = next(item for item in result["items"] if item["indicator_id"] == "financial-ebitda")
    assert ebitda["value"] == 12.5
    assert ebitda["unit_values"] == {"consolidated": 12.5}
    service.get_snapshot.assert_called_with(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )


def test_commercial_provider_exposes_consolidated_unit_values_on_branch_view() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = CommercialMetricsSnapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        matrix_rol_value=100.0,
        branch_rol_value=80.0,
        sales_conversion_rate_pct=62.0,
        sales_order_otd_pct=91.0,
        new_business_rol_pct=15.0,
        requested_branch="02",
    )

    provider = CommercialIndicatorsSnapshotProvider(
        commercial_metrics_snapshot_service=service,
    )
    result = provider.get_commercial_indicators_snapshot(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch="02",
    )

    closing = next(
        item for item in result["items"] if item["indicator_id"] == "commercial-closing-rate"
    )
    assert closing["value"] == 62.0
    assert closing["unit_values"] == {"consolidated": 62.0}
    service.get_snapshot.assert_called_with(
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )
