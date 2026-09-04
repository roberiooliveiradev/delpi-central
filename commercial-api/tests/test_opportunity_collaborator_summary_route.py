"""GET /analytics/opportunity-collaborator-summary — SQL summary via api-delpi (sem agregação truncada)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes import analytics_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/analytics/opportunity-collaborator-summary") -> Request:
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


def test_analytics_routes_bind_ok_fail() -> None:
    assert callable(analytics_routes.ok)
    assert callable(analytics_routes.fail)


def test_collaborator_summary_returns_envelope() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "success": True,
        "data": {
            "items": [
                {
                    "seller_code": "001",
                    "seller_name": "Ana",
                    "open_count": 35,
                    "won_count": 11,
                    "lost_count": 0,
                    "total_count": 46,
                    "age_days_avg": 15.3,
                }
            ],
            "source_count": 46,
            "truncated": False,
        },
    }
    request = _request()
    request.state.user = _User(["commercial.access"])
    unrestricted = CommercialCustomerScope(unrestricted=True, allowed_customers=None)

    with (
        patch.object(
            analytics_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            analytics_routes,
            "resolve_analytics_portfolio_scope",
            return_value=unrestricted,
        ),
    ):
        response = analytics_routes.bff_opportunity_collaborator_summary(request)

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_opportunity_collaborator_summary"
    assert body["data"]["items"][0]["sellerCode"] == "001"
    assert body["data"]["items"][0]["wonCount"] == 11
    assert body["data"]["sourceCount"] == 46
    assert body["data"]["truncated"] is False
    gateway.get_commercial_analytics.assert_called_once()
    path = gateway.get_commercial_analytics.call_args.args[0]
    assert path == "/proposals/collaborator-summary"
    params = gateway.get_commercial_analytics.call_args.kwargs.get("params") or {}
    assert "status" not in params


def test_collaborator_summary_gateway_down_returns_502_envelope() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.side_effect = RuntimeError("api-delpi indisponível.")
    request = _request()
    request.state.user = _User(["commercial.access"])
    unrestricted = CommercialCustomerScope(unrestricted=True, allowed_customers=None)

    with (
        patch.object(
            analytics_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            analytics_routes,
            "resolve_analytics_portfolio_scope",
            return_value=unrestricted,
        ),
    ):
        response = analytics_routes.bff_opportunity_collaborator_summary(request)

    assert response.status_code == 502
    body = json.loads(response.body)
    assert body["success"] is False
    assert "detail" not in body
    assert body["meta"]["operationId"] == "bff_opportunity_collaborator_summary"
