"""GetPortfolioBillingShareUseCase + rota BFF — KPI-PORTFOLIO-SHARE."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_portfolio_billing_share import (
    ROL_SUMMARY_PATH,
    NATURE_PORTFOLIO_BILLING_SHARE,
    GetPortfolioBillingShareUseCase,
    compute_share_pct,
    extract_rol_from_target_payload,
    resolve_rol_branches_for_branch,
)
from commercial_app.interface.http.routes import analytics_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/analytics/portfolio-billing-share") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_compute_share_pct_rounds_one_decimal() -> None:
    assert compute_share_pct(12.34, 100) == 12.3
    assert compute_share_pct(10, 0) is None
    assert compute_share_pct(0, 50) == 0.0


def test_extract_rol_prefers_rol_field() -> None:
    assert extract_rol_from_target_payload({"success": True, "data": {"rol": 42.5}}) == 42.5
    assert extract_rol_from_target_payload({"rol": 7}) == 7.0
    assert extract_rol_from_target_payload(None) == 0.0


def test_resolve_rol_branches_for_branch() -> None:
    assert resolve_rol_branches_for_branch(None) == ("01", "02")
    assert resolve_rol_branches_for_branch("01") == ("01",)
    assert resolve_rol_branches_for_branch("02") == ("02",)


def test_use_case_share_portfolio_over_company() -> None:
    gateway = MagicMock()

    def _analytics(path: str, *, params=None):
        codes = (params or {}).get("customer_codes")
        branch_code = (params or {}).get("branch")
        if path != ROL_SUMMARY_PATH:
            raise AssertionError(path)
        if branch_code == "01":
            return {"data": {"rol": 40.0 if codes else 200.0}}
        if branch_code == "02":
            return {"data": {"rol": 10.0 if codes else 50.0}}
        raise AssertionError(branch_code)

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
    assert data["nature"] == "gross"
    assert data["billingNature"] == "gross"
    assert data["kpiNature"] == NATURE_PORTFOLIO_BILLING_SHARE
    assert data["startDate"] == "2026-01-01"
    assert gateway.get_commercial_analytics.call_count == 4


def test_use_case_share_net_uses_rol_field() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {"rol": 80.0, "gross_revenue": 120.0}
    }
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    data = GetPortfolioBillingShareUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        branch="01",
        nature="net",
    )
    assert data["portfolioRol"] == 80.0
    assert data["nature"] == "net"


def test_use_case_share_gross_uses_gross_revenue() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {"rol": 80.0, "gross_revenue": 120.0}
    }
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    data = GetPortfolioBillingShareUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        branch="01",
        nature="gross",
    )
    assert data["portfolioRol"] == 120.0
    assert data["nature"] == "gross"


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
    assert all(
        c.args[0] == ROL_SUMMARY_PATH and c.kwargs.get("params", {}).get("branch") == "01"
        for c in gateway.get_commercial_analytics.call_args_list
    )
    assert gateway.get_commercial_analytics.call_count == 2


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


def test_portfolio_billing_share_route_ok() -> None:
    gateway = MagicMock()

    def _analytics(path: str, *, params=None):
        codes = (params or {}).get("customer_codes")
        branch_code = (params or {}).get("branch")
        if path != ROL_SUMMARY_PATH:
            raise AssertionError(path)
        if branch_code == "01":
            return {"data": {"rol": 30.0 if codes else 100.0}}
        if branch_code == "02":
            return {"data": {"rol": 20.0 if codes else 100.0}}
        raise AssertionError(branch_code)

    gateway.get_commercial_analytics.side_effect = _analytics
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    request = _request()
    request.state.user = _User(["commercial.manage"])

    with (
        patch.object(
            analytics_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            analytics_routes,
            "resolve_analytics_portfolio_scope",
            return_value=scope,
        ),
    ):
        response = analytics_routes.bff_portfolio_billing_share(
            request,
            start_date="2026-01-01",
            end_date="2026-01-31",
            branch=None,
            customer_segment=None,
            seller_id="p1",
            portfolio_id=None,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_get_analytics_portfolio_billing_share"
    assert body["data"]["portfolioRol"] == 50.0
    assert body["data"]["companyRol"] == 200.0
    assert body["data"]["sharePct"] == 25.0


def test_portfolio_billing_share_route_accepts_manage_permission() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {"data": {"rol": 10}}
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    request = _request()
    request.state.user = _User(["commercial.manage"])

    with (
        patch.object(
            analytics_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            analytics_routes,
            "resolve_analytics_portfolio_scope",
            return_value=scope,
        ),
    ):
        response = analytics_routes.bff_portfolio_billing_share(
            request,
            start_date="2026-01-01",
            end_date="2026-01-31",
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["data"]["sharePct"] == 100.0


def test_portfolio_billing_share_route_forbids_access_only() -> None:
    request = _request()
    request.state.user = _User(["commercial.access"])
    response = analytics_routes.bff_portfolio_billing_share(
        request,
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    assert response.status_code == 403
