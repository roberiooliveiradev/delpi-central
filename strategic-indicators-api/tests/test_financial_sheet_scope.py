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


def _build_service(
    *,
    ebitda: dict,
    fixed_cost: dict,
    pmr: dict,
    rol_by_branch: dict[str, dict],
) -> FinancialMetricsSnapshotService:
    sheets_gateway = MagicMock()
    sheets_gateway.get_ebitda_pct.return_value = ebitda
    sheets_gateway.get_fixed_cost_pct.return_value = fixed_cost
    sheets_gateway.get_pmr.return_value = pmr

    financial_gateway = MagicMock()
    financial_gateway.list_rol_by_branch.return_value = rol_by_branch

    return FinancialMetricsSnapshotService(
        financial_sheets_gateway=sheets_gateway,
        financial_gateway=financial_gateway,
    )


def test_build_snapshot_uses_api_pct_without_rol_division() -> None:
    service = _build_service(
        ebitda={
            "ebitda_over_rol_pct": 13.5,
            "branches": [{"branch": "01", "ebitda_over_rol_pct": 11.0}],
        },
        fixed_cost={
            "fixed_cost_over_rol_pct": 14.0,
            "branches": [{"branch": "01", "fixed_cost_over_rol_pct": 12.0}],
        },
        pmr={"pmr_days": None, "branches": []},
        rol_by_branch={"01": {"rol": 1_000_000}},
    )

    snapshot = service._build_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch=None,
    )

    consolidated = next(
        item for item in snapshot.branches if item.branch == CONSOLIDATED_BRANCH_KEY
    )
    branch_01 = next(item for item in snapshot.branches if item.branch == "01")

    assert consolidated.ebitda_over_rol_pct == 13.5
    assert consolidated.fixed_cost_over_rol_pct == 14.0
    assert branch_01.ebitda_over_rol_pct == 11.0
    assert branch_01.fixed_cost_over_rol_pct == 12.0


def test_build_snapshot_returns_none_when_branch_has_no_sheet_rows() -> None:
    service = _build_service(
        ebitda={
            "ebitda_over_rol_pct": 0.0,
            "branches": [{"branch": "01", "ebitda_over_rol_pct": 0.0}],
        },
        fixed_cost={
            "fixed_cost_over_rol_pct": 0.0,
            "branches": [],
        },
        pmr={"pmr_days": None, "branches": []},
        rol_by_branch={"01": {"rol": 1_000_000}},
    )

    snapshot = service._build_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch=None,
    )

    branch_01 = next(item for item in snapshot.branches if item.branch == "01")

    assert branch_01.ebitda_over_rol_pct == 0.0
    assert branch_01.fixed_cost_over_rol_pct is None


def test_build_snapshot_returns_none_pmr_without_receivables_rows() -> None:
    service = _build_service(
        ebitda={
            "ebitda_over_rol_pct": 10.0,
            "branches": [{"branch": "02", "ebitda_over_rol_pct": 10.0}],
        },
        fixed_cost={"fixed_cost_over_rol_pct": 0.0, "branches": []},
        pmr={"pmr_days": None, "branches": []},
        rol_by_branch={"02": {"rol": 500_000}},
    )

    snapshot = service._build_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch=None,
    )

    branch_02 = next(item for item in snapshot.branches if item.branch == "02")

    assert branch_02.pmr_days is None


def test_build_snapshot_keeps_zero_pmr_when_sheet_has_zero() -> None:
    service = _build_service(
        ebitda={"ebitda_over_rol_pct": 0.0, "branches": []},
        fixed_cost={"fixed_cost_over_rol_pct": 0.0, "branches": []},
        pmr={
            "pmr_days": 0.0,
            "branches": [{"branch": "02", "pmr_days": 0.0}],
        },
        rol_by_branch={"02": {"rol": 500_000}},
    )

    snapshot = service._build_snapshot(
        start_date="01-05-2026",
        end_date="31-05-2026",
        branch=None,
    )

    branch_02 = next(item for item in snapshot.branches if item.branch == "02")

    assert branch_02.pmr_days == 0.0
