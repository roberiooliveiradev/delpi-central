"""GetPortfolioBillingRankingUseCase — delta % por cliente/vendedor."""

from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_portfolio_billing_ranking import (
    NATURE_PORTFOLIO_BILLING_RANKING,
    GetPortfolioBillingRankingUseCase,
    compute_delta_pct,
    shift_iso_date_by_years,
)


def test_shift_iso_date_by_years_clamps_leap_day() -> None:
    assert shift_iso_date_by_years("2024-02-29", -1) == "2023-02-28"
    assert shift_iso_date_by_years("2026-08-14", -1) == "2025-08-14"


def test_compute_delta_pct() -> None:
    assert compute_delta_pct(110, 100) == 10.0
    assert compute_delta_pct(90, 100) == -10.0
    assert compute_delta_pct(10, 0) is None


def test_use_case_ranks_customers_by_delta_pct() -> None:
    gateway = MagicMock()

    def _analytics(path: str, *, params=None):
        assert path == "/rol/by-customer"
        start = (params or {}).get("start_date")
        if str(start).startswith("2026"):
            return {
                "data": {
                    "items": [
                        {
                            "customer_code": "100",
                            "customer_store": "01",
                            "customer_name": "Alta",
                            "rol_with_ipi": 200,
                        },
                        {
                            "customer_code": "200",
                            "customer_store": "01",
                            "customer_name": "Queda",
                            "rol_with_ipi": 50,
                        },
                    ]
                }
            }
        return {
            "data": {
                "items": [
                    {
                        "customer_code": "100",
                        "customer_store": "01",
                        "customer_name": "Alta",
                        "rol_with_ipi": 100,
                    },
                    {
                        "customer_code": "200",
                        "customer_store": "01",
                        "customer_name": "Queda",
                        "rol_with_ipi": 100,
                    },
                ]
            }
        }

    gateway.get_commercial_analytics.side_effect = _analytics
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01"), ("200", "01")}),
    )
    data = GetPortfolioBillingRankingUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        limit=10,
    )
    assert data["nature"] == NATURE_PORTFOLIO_BILLING_RANKING
    assert data["groupBy"] == "customer"
    assert data["items"][0]["customerCode"] == "100"
    assert data["items"][0]["deltaPct"] == 100.0
    assert data["items"][1]["customerCode"] == "200"
    assert data["items"][1]["deltaPct"] == -50.0
    assert data["order"] == "growth"


def test_use_case_order_decline_puts_worst_delta_first() -> None:
    gateway = MagicMock()

    def _analytics(path: str, *, params=None):
        start = (params or {}).get("start_date")
        if str(start).startswith("2026"):
            return {
                "data": {
                    "items": [
                        {
                            "customer_code": "100",
                            "customer_store": "01",
                            "customer_name": "Alta",
                            "rol_with_ipi": 200,
                        },
                        {
                            "customer_code": "200",
                            "customer_store": "01",
                            "customer_name": "Queda",
                            "rol_with_ipi": 50,
                        },
                        {
                            "customer_code": "300",
                            "customer_store": "01",
                            "customer_name": "Pior",
                            "rol_with_ipi": 10,
                        },
                    ]
                }
            }
        return {
            "data": {
                "items": [
                    {
                        "customer_code": "100",
                        "customer_store": "01",
                        "customer_name": "Alta",
                        "rol_with_ipi": 100,
                    },
                    {
                        "customer_code": "200",
                        "customer_store": "01",
                        "customer_name": "Queda",
                        "rol_with_ipi": 100,
                    },
                    {
                        "customer_code": "300",
                        "customer_store": "01",
                        "customer_name": "Pior",
                        "rol_with_ipi": 100,
                    },
                ]
            }
        }

    gateway.get_commercial_analytics.side_effect = _analytics
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    data = GetPortfolioBillingRankingUseCase().execute(
        gateway,
        scope,
        start_date="2026-01-01",
        end_date="2026-01-31",
        limit=2,
        order="decline",
    )
    assert data["order"] == "decline"
    assert [row["customerCode"] for row in data["items"]] == ["300", "200"]
    assert data["items"][0]["deltaPct"] == -90.0


def test_use_case_group_by_seller() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {
            "items": [
                {
                    "customer_code": "100",
                    "customer_store": "01",
                    "customer_name": "A",
                    "rol_with_ipi": 100,
                },
                {
                    "customer_code": "200",
                    "customer_store": "01",
                    "customer_name": "B",
                    "rol_with_ipi": 50,
                },
            ]
        }
    }
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    data = GetPortfolioBillingRankingUseCase().execute(
        gateway,
        scope,
        start_date="2026-02-01",
        end_date="2026-02-28",
        group_by="seller",
        seller_name_by_customer={
            ("100", "01"): "Ana",
            ("200", "01"): "Ana",
        },
    )
    assert data["groupBy"] == "seller"
    assert len(data["items"]) == 1
    assert data["items"][0]["sellerName"] == "Ana"
    assert data["items"][0]["currentRol"] == 150.0


import json
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.interface.http.routes import analytics_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/analytics/portfolio-billing-ranking") -> Request:
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


def test_portfolio_billing_ranking_route_ok_for_accounts_view() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {
            "items": [
                {
                    "customer_code": "100",
                    "customer_store": "01",
                    "customer_name": "Cli",
                    "rol_with_ipi": 120,
                }
            ]
        }
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    request = _request()
    request.state.user = _User(["commercial.access"])

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
        response = analytics_routes.bff_portfolio_billing_ranking(
            request,
            start_date="2026-01-01",
            end_date="2026-01-31",
            group_by="customer",
            limit=20,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_get_analytics_portfolio_billing_ranking"
    assert body["data"]["nature"] == NATURE_PORTFOLIO_BILLING_RANKING
    assert body["data"]["groupBy"] == "customer"


def test_portfolio_billing_ranking_route_seller_forbidden_without_team() -> None:
    request = _request()
    request.state.user = _User(["commercial.access"])
    response = analytics_routes.bff_portfolio_billing_ranking(
        request,
        start_date="2026-01-01",
        end_date="2026-01-31",
        group_by="seller",
    )
    assert response.status_code == 403
