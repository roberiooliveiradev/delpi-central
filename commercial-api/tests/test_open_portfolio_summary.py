"""GET /analytics/open-portfolio-summary — KPI-CARTEIRA BFF."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_open_portfolio_summary import (
    GetOpenPortfolioSummaryUseCase,
    NATURE_OPEN_ORDER_VALUE,
)
from commercial_app.interface.http.routes import analytics_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/analytics/open-portfolio-summary") -> Request:
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


_FIXED_AS_OF = datetime(2026, 8, 13, 18, 0, 0, tzinfo=timezone.utc)


def test_use_case_empty_portfolio_returns_zeros() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        portfolio_id="p-empty",
        message="vazia",
    )
    raw = {
        "items": [
            {
                "codigo_cadastro": "100",
                "loja_cadastro": "01",
                "valor_aberto": 250.5,
            }
        ],
        "summary": {"total_linhas": 1, "valor_total_aberto": 250.5},
    }
    data = GetOpenPortfolioSummaryUseCase().execute(raw, scope, as_of=_FIXED_AS_OF)
    assert data == {
        "openValue": 0.0,
        "openLineCount": 0,
        "asOf": _FIXED_AS_OF.isoformat(),
        "nature": NATURE_OPEN_ORDER_VALUE,
    }
    assert "items" not in data


def test_use_case_sums_valor_aberto_in_scope() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01"), ("200", "01")}),
    )
    raw = {
        "items": [
            {
                "codigo_cadastro": "100",
                "loja_cadastro": "01",
                "valor_aberto": 10,
                "saldo": 1,
                "no_estoque": 1,
            },
            {
                "codigo_cadastro": "200",
                "loja_cadastro": "01",
                "valor_aberto": 15.5,
                "saldo": 1,
                "no_estoque": 0,
            },
            {
                "codigo_cadastro": "999",
                "loja_cadastro": "01",
                "valor_aberto": 999,
                "saldo": 1,
                "no_estoque": 0,
            },
        ]
    }
    data = GetOpenPortfolioSummaryUseCase().execute(raw, scope, as_of=_FIXED_AS_OF)
    assert data["openValue"] == 25.5
    assert data["openLineCount"] == 2
    assert data["nature"] == NATURE_OPEN_ORDER_VALUE
    assert data["asOf"] == _FIXED_AS_OF.isoformat()
    assert "items" not in data


def test_open_portfolio_summary_route_empty_portfolio() -> None:
    gateway = MagicMock()
    gateway.list_open_orders.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "codigo_cadastro": "100",
                    "loja_cadastro": "01",
                    "valor_aberto": 40,
                }
            ]
        },
    }
    empty_scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        portfolio_id="p1",
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
            return_value=empty_scope,
        ),
    ):
        response = analytics_routes.bff_open_portfolio_summary(
            request,
            seller_id="p1",
            portfolio_id=None,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_get_analytics_open_portfolio_summary"
    assert body["data"]["openValue"] == 0.0
    assert body["data"]["openLineCount"] == 0
    assert body["data"]["nature"] == NATURE_OPEN_ORDER_VALUE
    assert "items" not in body["data"]
    gateway.list_open_orders.assert_called_once()


def test_open_portfolio_summary_route_with_items() -> None:
    gateway = MagicMock()
    gateway.list_open_orders.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "codigo_cadastro": "100",
                    "loja_cadastro": "01",
                    "valor_aberto": 10,
                    "saldo": 1,
                    "no_estoque": 1,
                },
                {
                    "codigo_cadastro": "100",
                    "loja_cadastro": "01",
                    "valor_aberto": 20,
                    "saldo": 2,
                    "no_estoque": 0,
                },
                {
                    "codigo_cadastro": "999",
                    "loja_cadastro": "01",
                    "valor_aberto": 500,
                    "saldo": 1,
                    "no_estoque": 0,
                },
            ]
        },
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
        response = analytics_routes.bff_open_portfolio_summary(
            request,
            seller_id="p1",
            portfolio_id=None,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["data"]["openValue"] == 30.0
    assert body["data"]["openLineCount"] == 2
    assert body["data"]["nature"] == NATURE_OPEN_ORDER_VALUE
    assert "items" not in body["data"]


def test_open_portfolio_summary_403_without_access() -> None:
    request = _request()
    request.state.user = _User(["commercial.billing.notify"])
    response = analytics_routes.bff_open_portfolio_summary(
        request,
        seller_id=None,
        portfolio_id=None,
    )
    assert response.status_code == 403
