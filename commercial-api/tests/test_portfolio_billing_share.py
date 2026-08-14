"""GetPortfolioBillingShareUseCase — KPI-PORTFOLIO-SHARE."""

from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_portfolio_billing_share import (
    BRANCH_ROL_PATH,
    HEAD_OFFICE_ROL_PATH,
    NATURE_PORTFOLIO_BILLING_SHARE,
    GetPortfolioBillingShareUseCase,
    compute_share_pct,
    extract_rol_from_target_payload,
    resolve_rol_paths_for_branch,
)


def test_compute_share_pct_rounds_one_decimal() -> None:
    assert compute_share_pct(12.34, 100) == 12.3
    assert compute_share_pct(10, 0) is None
    assert compute_share_pct(0, 50) == 0.0


def test_extract_rol_prefers_rol_field() -> None:
    assert extract_rol_from_target_payload({"success": True, "data": {"rol": 42.5}}) == 42.5
    assert extract_rol_from_target_payload({"rol_with_ipi": 7}) == 7.0
    assert extract_rol_from_target_payload(None) == 0.0


def test_resolve_rol_paths_for_branch() -> None:
    assert resolve_rol_paths_for_branch(None) == (HEAD_OFFICE_ROL_PATH, BRANCH_ROL_PATH)
    assert resolve_rol_paths_for_branch("01") == (HEAD_OFFICE_ROL_PATH,)
    assert resolve_rol_paths_for_branch("02") == (BRANCH_ROL_PATH,)


def test_use_case_share_portfolio_over_company() -> None:
    gateway = MagicMock()

    def _analytics(path: str, *, params=None):
        codes = (params or {}).get("customer_codes")
        if path == HEAD_OFFICE_ROL_PATH:
            return {"data": {"rol": 40.0 if codes else 200.0}}
        if path == BRANCH_ROL_PATH:
            return {"data": {"rol": 10.0 if codes else 50.0}}
        raise AssertionError(path)

    gateway.get_commercial_analytics.side_effect = _analytics
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    data = GetPortfolioBillingShareUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        branch=None,
    )
    assert data["portfolioRol"] == 50.0
    assert data["companyRol"] == 250.0
    assert data["sharePct"] == 20.0
    assert data["nature"] == NATURE_PORTFOLIO_BILLING_SHARE
    assert data["startDate"] == "2026-01-01"
    assert gateway.get_commercial_analytics.call_count == 4


def test_use_case_branch_01_only_head_office() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {"data": {"rol": 100.0}}
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    data = GetPortfolioBillingShareUseCase().execute(
        gateway,
        scope,
        start_date="2026-02-01",
        end_date="2026-02-28",
        branch="01",
    )
    assert data["portfolioRol"] == 100.0
    assert data["companyRol"] == 100.0
    assert data["sharePct"] == 100.0
    paths = [c.kwargs.get("params") and c.args[0] for c in gateway.get_commercial_analytics.call_args_list]
    # two calls (portfolio + company), both head office
    assert all(c.args[0] == HEAD_OFFICE_ROL_PATH for c in gateway.get_commercial_analytics.call_args_list)
    assert len(paths) == 2


def test_use_case_company_zero_share_null() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {"data": {"rol": 0}}
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("1", "01")}),
    )
    data = GetPortfolioBillingShareUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        branch="02",
    )
    assert data["sharePct"] is None
    assert data["portfolioRol"] == 0.0
    assert data["companyRol"] == 0.0
