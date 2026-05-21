from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.financial.financial_metrics_snapshot_service import (
    FinancialMetricsSnapshotService,
)
from si_app.application.services.financial.financial_sheet_scope import (
    CONSOLIDATED_BRANCH_KEY,
    is_consolidated_sheet_row,
)


def test_is_consolidated_sheet_row() -> None:
    assert is_consolidated_sheet_row(None) is True
    assert is_consolidated_sheet_row("") is True
    assert is_consolidated_sheet_row("  ") is True
    assert is_consolidated_sheet_row("01") is False


def test_build_snapshot_uses_sheet_pct_without_rol_division() -> None:
    service = FinancialMetricsSnapshotService(
        ebitda_repository=MagicMock(),
        fixed_cost_repository=MagicMock(),
        receivables_repository=MagicMock(),
        financial_query_repository=MagicMock(),
    )
    service._financial_query_repository.list_rol_by_branch.return_value = {
        "01": {"rol_with_ipi": 1_000_000},
    }

    snapshot = service._build_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch=None,
        rows_override={
            "ebitda_rows": [
                {"filial": "", "data": "15-05-2026", "ebitida": 13.5},
                {"filial": "01", "data": "15-05-2026", "ebitida": 11.0},
            ],
            "fixed_cost_rows": [
                {"filial": "", "data": "15-05-2026", "custos_fixos": 14.0},
                {"filial": "01", "data": "15-05-2026", "custos_fixos": 12.0},
            ],
            "receivables_rows": [],
        },
    )

    consolidated = next(
        item for item in snapshot.branches if item.branch == CONSOLIDATED_BRANCH_KEY
    )
    branch_01 = next(item for item in snapshot.branches if item.branch == "01")

    assert consolidated.ebitda_over_rol_pct == 13.5
    assert consolidated.fixed_cost_over_rol_pct == 14.0
    assert branch_01.ebitda_over_rol_pct == 11.0
    assert branch_01.fixed_cost_over_rol_pct == 12.0
