"""BFF /analytics/rol/by-product e /rol/by-customer — membership + proxy."""

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


def _request(
    path: str,
    *,
    query: bytes = b"",
) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query,
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_bff_rol_by_product_merges_membership_and_product_filters() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {
            "items": [],
            "summary": {"total_rol": 0, "items_count": 0},
            "export_destination_countries": [],
        }
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01"), ("200", "01")}),
    )
    request = _request(
        "/analytics/rol/by-product",
        query=b"customer_codes=100",
    )
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
        response = analytics_routes.bff_rol_by_product(
            request,
            start_date="2026-01-01",
            end_date="2026-01-31",
            branch=None,
            customer_segment=None,
            product_codes="90A",
            product_groups="3019",
            market="domestic",
            group_by="product_group",
            limit=100,
            seller_id=None,
            portfolio_id=None,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_get_commercial_rol_by_product"
    gateway.get_commercial_analytics.assert_called_once()
    path, kwargs = gateway.get_commercial_analytics.call_args
    assert path[0] == "/rol/by-product"
    params = kwargs["params"]
    assert params["customer_codes"] == "100"
    assert params["product_codes"] == "90A"
    assert params["product_groups"] == "3019"
    assert params["market"] == "domestic"
    assert params["group_by"] == "product_group"


def test_bff_rol_by_customer_passes_through_envelope() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "data": {
            "items": [
                {
                    "customer_code": "1",
                    "customer_name": "ACME",
                    "cnpj": "00",
                    "city": "Joinville",
                    "state": "SC",
                    "share_pct": 10.0,
                }
            ],
            "summary": {"total_rol": 1},
        }
    }
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    request = _request("/analytics/rol/by-customer")
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
        response = analytics_routes.bff_rol_by_customer(
            request,
            start_date="2026-01-01",
            end_date="2026-01-31",
            branch=None,
            customer_segment=None,
            product_codes=None,
            product_groups=None,
            market=None,
            limit=500,
            include_others=False,
            seller_id=None,
            portfolio_id=None,
        )

    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["meta"]["operationId"] == "bff_get_commercial_rol_by_customer"
    assert body["data"]["items"][0]["cnpj"] == "00"
    path, kwargs = gateway.get_commercial_analytics.call_args
    assert path[0] == "/rol/by-customer"
    assert "customer_codes" not in kwargs["params"]
    assert kwargs["params"]["include_others"] is False
