from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialBranchSnapshot,
    FinancialMetricsSnapshot,
)
from app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
)
from app.application.use_cases.financial.get_financial_ebitda_pct_use_case import (
    GetFinancialEbitdaPctUseCase,
)
from app.application.use_cases.financial.get_financial_fixed_cost_pct_use_case import (
    GetFinancialFixedCostPctUseCase,
)


def _empty_snapshot() -> FinancialMetricsSnapshot:
    return FinancialMetricsSnapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branches=[
            FinancialBranchSnapshot(
                branch=CONSOLIDATED_BRANCH_KEY,
                rol_with_ipi=1_000_000.0,
                ebitda_value=0.0,
                fixed_cost_value=0.0,
                pmr_days=None,
                ebitda_over_rol_pct=None,
                fixed_cost_over_rol_pct=None,
            ),
        ],
    )


def test_ebitda_pct_returns_null_when_sheet_has_no_rows() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = _empty_snapshot()
    use_case = GetFinancialEbitdaPctUseCase(service)

    result = use_case.execute(
        GetRolRequest(start_date="01-05-2026", end_date="31-05-2026", branch=None)
    )

    assert result["ebitda_over_rol_pct"] is None


def test_fixed_cost_pct_returns_null_when_sheet_has_no_rows() -> None:
    service = MagicMock()
    service.get_snapshot.return_value = _empty_snapshot()
    use_case = GetFinancialFixedCostPctUseCase(service)

    result = use_case.execute(
        GetRolRequest(start_date="01-05-2026", end_date="31-05-2026", branch=None)
    )

    assert result["fixed_cost_over_rol_pct"] is None
