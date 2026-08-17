"""BFF recently-closed open-orders — membership filter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes import open_orders_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/open-orders/recently-closed") -> Request:
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


def test_recently_closed_bff_filters_via_scope() -> None:
    gateway = MagicMock()
    gateway.list_recently_closed_orders.return_value = {
        "success": True,
        "data": {
            "items": [
                {"codigo_cadastro": "100", "loja_cadastro": "01", "valor_aberto": 10},
                {"codigo_cadastro": "999", "loja_cadastro": "01", "valor_aberto": 50},
            ],
            "summary": {"total_linhas": 2},
        },
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope

    request = _request()
    request.state.user = _User(["commercial.access"])

    with (
        patch.object(
            open_orders_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            open_orders_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(open_orders_routes, "actor_sub_from_request", return_value="u1"),
    ):
        response = open_orders_routes.list_commercial_recently_closed_orders(
            request,
            days=30,
            seller_id=None,
            portfolio_id=None,
        )

    import json

    body = json.loads(response.body)
    assert response.status_code == 200
    assert body["success"] is True
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["codigo_cadastro"] == "100"
    assert body["data"]["summary"]["days"] == 30
    gateway.list_recently_closed_orders.assert_called_once_with(days=30)
