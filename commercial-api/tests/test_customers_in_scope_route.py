"""BFF GET /customers/in-scope — membership + metrics."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes import customer_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/customers/in-scope") -> Request:
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


def test_list_customers_in_scope_returns_membership_items() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000204", "01"), ("000100", "01")}),
        portfolio_id="p1",
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope

    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "customer_code": "000204",
                "customer_store": "01",
                "customer_name": "AHT",
                "open_value": 0.0,
                "has_overdue": False,
                "has_open_orders": False,
            },
            {
                "customer_code": "000100",
                "customer_store": "01",
                "customer_name": "Com aberto",
                "open_value": 99.0,
                "has_overdue": False,
                "has_open_orders": True,
            },
        ],
        "summary": {
            "customer_count": 2,
            "open_value_total": 99.0,
            "overdue_customer_count": 0,
        },
        "empty_portfolio": False,
        "message": None,
        "metrics": {"available": True, "reason": None},
    }

    request = _request()
    request.state.user = _User(["commercial.access"])

    with (
        patch.object(
            customer_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(
            customer_routes,
            "build_list_customers_in_scope_use_case",
            return_value=use_case,
        ),
        patch.object(customer_routes, "actor_sub_from_request", return_value="u1"),
        patch.object(
            customer_routes,
            "current_user_from_request",
            return_value=request.state.user,
        ),
        patch.object(customer_routes, "can_manage_portfolios", return_value=False),
        patch.object(customer_routes, "can_use_team_scope", return_value=False),
    ):
        response = customer_routes.list_customers_in_scope(
            request,
            seller_id="p1",
            portfolio_id=None,
        )

    payload = json.loads(response.body.decode())
    assert payload["success"] is True
    data = payload["data"]
    assert data["summary"]["customer_count"] == 2
    codes = {item["customer_code"] for item in data["items"]}
    assert "000204" in codes
    scope_svc.execute.assert_called_once()
    assert scope_svc.execute.call_args.kwargs["portfolio_id"] == "p1"
    use_case.execute.assert_called_once_with(scope)


def test_list_customers_in_scope_empty_portfolio() -> None:
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        message="Sua carteira ainda não possui clientes vinculados.",
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "summary": {
            "customer_count": 0,
            "open_value_total": 0.0,
            "overdue_customer_count": 0,
        },
        "empty_portfolio": True,
        "message": scope.message,
        "metrics": {"available": True, "reason": None},
    }

    request = _request()
    request.state.user = _User(["commercial.access"])

    with (
        patch.object(
            customer_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(
            customer_routes,
            "build_list_customers_in_scope_use_case",
            return_value=use_case,
        ),
        patch.object(customer_routes, "actor_sub_from_request", return_value="u1"),
        patch.object(
            customer_routes,
            "current_user_from_request",
            return_value=request.state.user,
        ),
        patch.object(customer_routes, "can_manage_portfolios", return_value=False),
        patch.object(customer_routes, "can_use_team_scope", return_value=False),
    ):
        response = customer_routes.list_customers_in_scope(
            request, seller_id=None, portfolio_id=None
        )

    payload = json.loads(response.body.decode())
    assert payload["data"]["empty_portfolio"] is True
    assert payload["data"]["items"] == []
