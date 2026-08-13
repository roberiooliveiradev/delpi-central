"""GET /analytics/open-portfolio-horizon — KPI-CARTEIRA-HORIZON BFF."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_open_portfolio_horizon import (
    GetOpenPortfolioHorizonUseCase,
)
from commercial_app.domain.services.open_orders_horizon_bucket_service import (
    BUCKET_CURRENT_MONTH,
    BUCKET_OVERDUE,
    HORIZON_TIMEZONE,
    NATURE_OPEN_ORDER_VALUE_BY_DELIVERY,
)
from commercial_app.interface.http.routes import analytics_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/analytics/open-portfolio-horizon") -> Request:
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


_AS_OF = datetime(2026, 8, 13, 12, 0, 0, tzinfo=ZoneInfo(HORIZON_TIMEZONE))


def test_horizon_use_case_buckets_in_scope() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
        portfolio_id="p1",
    )
    raw = {
        "items": [
            {
                "codigo_cadastro": "100",
                "loja_cadastro": "01",
                "valor_aberto": 10,
                "data_entrega": "2026-08-01",
            },
            {
                "codigo_cadastro": "100",
                "loja_cadastro": "01",
                "valor_aberto": 20,
                "data_entrega": "2026-08-20",
            },
            {
                "codigo_cadastro": "999",
                "loja_cadastro": "01",
                "valor_aberto": 999,
                "data_entrega": "2026-08-01",
            },
        ]
    }
    data = GetOpenPortfolioHorizonUseCase().execute(raw, scope, as_of=_AS_OF)
    assert data["nature"] == NATURE_OPEN_ORDER_VALUE_BY_DELIVERY
    assert data["scope"]["mode"] == "membership"
    assert data["scope"]["seller_id"] == "p1"
    by_id = {b["id"]: b for b in data["buckets"]}
    assert by_id[BUCKET_OVERDUE]["openValue"] == 10.0
    assert by_id[BUCKET_CURRENT_MONTH]["openValue"] == 20.0
    assert data["totals"]["openLineCount"] == 2
    assert "items" not in data


def test_horizon_route_requires_analytics_view() -> None:
    request = _request()
    request.state.user = _User([])
    response = analytics_routes.bff_open_portfolio_horizon(request)
    assert response.status_code == 403


def test_horizon_route_ok() -> None:
    gateway = MagicMock()
    gateway.list_open_orders.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "codigo_cadastro": "100",
                    "loja_cadastro": "01",
                    "valor_aberto": 40,
                    "data_entrega": "2026-08-20",
                }
            ]
        },
    }
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    request = _request()
    request.state.user = _User(["commercial.analytics.view"])

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
        response = analytics_routes.bff_open_portfolio_horizon(request)

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["meta"]["operationId"] == "bff_get_analytics_open_portfolio_horizon"
    assert body["data"]["nature"] == NATURE_OPEN_ORDER_VALUE_BY_DELIVERY
    assert body["data"]["totals"]["openValue"] == 40.0
