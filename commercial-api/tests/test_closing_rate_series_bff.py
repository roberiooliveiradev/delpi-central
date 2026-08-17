"""GET /analytics/closing-rate/series — BFF proxy da série de hit rate."""

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


def _request(path: str = "/analytics/closing-rate/series") -> Request:
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


def test_closing_rate_series_proxies_to_api_delpi() -> None:
    gateway = MagicMock()
    gateway.get_commercial_analytics.return_value = {
        "success": True,
        "data": {
            "granularity": "month",
            "truncated": False,
            "points": [
                {
                    "periodo": "ago/2026",
                    "sort_key": "2026-08",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-13",
                    "conversion_filial_01": 25.0,
                    "conversion_filial_02": 10.0,
                    "qtd_proposals_01": 20,
                    "qtd_proposals_02": 10,
                    "qtd_won_01": 5,
                    "qtd_won_02": 1,
                }
            ],
        },
    }
    scope = CommercialCustomerScope(
        unrestricted=True,
        allowed_customers=frozenset(),
    )

    req = _request()
    req.state.user = _User(["commercial.access"])

    with (
        patch.object(
            analytics_routes,
            "resolve_analytics_portfolio_scope",
            return_value=scope,
        ),
        patch.object(
            analytics_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
    ):
        response = analytics_routes.bff_closing_rate_series(
            req,
            start_date="2026-08-01",
            end_date="2026-08-13",
            customer_segment=None,
            granularity="month",
            seller_id=None,
            portfolio_id=None,
        )

    body = json.loads(response.body.decode())
    assert body["success"] is True
    assert body["meta"]["operationId"] == "bff_get_sales_conversion_rate_series"
    assert body["data"]["points"][0]["conversion_filial_01"] == 25.0
    gateway.get_commercial_analytics.assert_called_once()
    path, kwargs = gateway.get_commercial_analytics.call_args[0][0], gateway.get_commercial_analytics.call_args[1]
    assert path == "/closing-rate/series"
    assert kwargs["params"]["granularity"] == "month"


def test_closing_rate_series_forbidden_without_permission() -> None:
    req = _request()
    req.state.user = _User([])

    with patch.object(
        analytics_routes,
        "resolve_analytics_portfolio_scope",
        side_effect=PermissionError("sem permissão"),
    ):
        response = analytics_routes.bff_closing_rate_series(
            req,
            start_date=None,
            end_date=None,
            customer_segment=None,
            granularity="month",
            seller_id=None,
            portfolio_id=None,
        )

    body = json.loads(response.body.decode())
    assert body["success"] is False
    assert response.status_code == 403
