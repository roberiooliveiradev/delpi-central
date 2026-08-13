"""Rotas BFF open-orders / billing / NF (escopo commercial + gateway mock)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes import customer_routes, open_orders_routes
from commercial_app.interface.http.schemas.portfolio_schemas import BillingSeriesBody


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub
        self.id = sub


def _request(path: str = "/open-orders/", method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_open_orders_bff_filters_via_scope() -> None:
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
                    "codigo_cadastro": "999",
                    "loja_cadastro": "01",
                    "valor_aberto": 50,
                    "saldo": 1,
                    "no_estoque": 0,
                },
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

    request = _request("/open-orders/")
    request.state.user = _User(["commercial.accounts.view"])

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
            response = open_orders_routes.list_commercial_open_orders(
                request,
                seller_id=None,
                portfolio_id=None,
            )

    assert response.status_code == 200
    import json

    body = json.loads(response.body)
    assert body["success"] is True
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["codigo_cadastro"] == "100"
    horizon = body["data"]["deliveryHorizon"]
    assert horizon["nature"] == "open_order_value_by_delivery"
    assert horizon["totals"]["openLineCount"] == 1
    assert horizon["totals"]["openValue"] == 10.0
    gateway.list_open_orders.assert_called_once()


def test_billing_series_bff_filters_pairs() -> None:
    gateway = MagicMock()
    gateway.list_customer_billing_series.return_value = {
        "success": True,
        "data": {"months": 12, "customer_count": 1, "points": []},
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope
    scope_svc.filter_pairs.return_value = [("100", "01")]

    request = _request("/customers/billing-series", method="POST")
    request.state.user = _User(["commercial.accounts.view"])
    body = BillingSeriesBody.model_validate(
        {
            "customers": [
                {"customer_code": "100", "customer_store": "01"},
                {"customer_code": "999", "customer_store": "01"},
            ],
            "months": 12,
        }
    )

    with (
        patch.object(
            customer_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            customer_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(customer_routes, "actor_sub_from_request", return_value="u1"),
    ):
        response = customer_routes.list_commercial_customer_billing_series(request, body)

    assert response.status_code == 200
    gateway.list_customer_billing_series.assert_called_once()
    payload = gateway.list_customer_billing_series.call_args.kwargs["payload"]
    assert payload["customers"] == [{"customer_code": "100", "customer_store": "01"}]


def test_billing_series_multi_select_dedupes_allowed_pairs() -> None:
    """Multi-select (2+ pares): membership + dedupe antes do gateway."""
    gateway = MagicMock()
    gateway.list_customer_billing_series.return_value = {
        "success": True,
        "data": {"months": 12, "customer_count": 2, "points": []},
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01"), ("200", "01")}),
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope
    scope_svc.filter_pairs.return_value = [
        ("100", "01"),
        ("200", "01"),
        ("100", "01"),
    ]

    request = _request("/customers/billing-series", method="POST")
    request.state.user = _User(["commercial.accounts.view"])
    body = BillingSeriesBody.model_validate(
        {
            "customers": [
                {"customer_code": "100", "customer_store": "01"},
                {"customer_code": "200", "customer_store": "01"},
                {"customer_code": "100", "customer_store": "01"},
                {"customer_code": "999", "customer_store": "01"},
            ],
            "months": 12,
            "granularity": "month",
        }
    )

    with (
        patch.object(
            customer_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            customer_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(customer_routes, "actor_sub_from_request", return_value="u1"),
    ):
        response = customer_routes.list_commercial_customer_billing_series(request, body)

    assert response.status_code == 200
    payload = gateway.list_customer_billing_series.call_args.kwargs["payload"]
    assert payload["customers"] == [
        {"customer_code": "100", "customer_store": "01"},
        {"customer_code": "200", "customer_store": "01"},
    ]
    assert payload["granularity"] == "month"


def test_billing_series_single_pair_skips_membership_filter() -> None:
    """Detalhe Conta (1 par): não aplica filter_pairs de carteira."""
    gateway = MagicMock()
    gateway.list_customer_billing_series.return_value = {
        "success": True,
        "data": {"months": 12, "customer_count": 1, "points": []},
    }
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("100", "01")}),
    )
    scope_svc = MagicMock()
    scope_svc.execute.return_value = scope

    request = _request("/customers/billing-series", method="POST")
    request.state.user = _User(["commercial.accounts.view"])
    body = BillingSeriesBody.model_validate(
        {
            "customers": [{"customer_code": "999", "customer_store": "01"}],
            "months": 12,
        }
    )

    with (
        patch.object(
            customer_routes,
            "build_delpi_commercial_gateway",
            return_value=gateway,
        ),
        patch.object(
            customer_routes,
            "build_resolve_commercial_customer_scope_service",
            return_value=scope_svc,
        ),
        patch.object(customer_routes, "actor_sub_from_request", return_value="u1"),
    ):
        response = customer_routes.list_commercial_customer_billing_series(request, body)

    assert response.status_code == 200
    scope_svc.filter_pairs.assert_not_called()
    payload = gateway.list_customer_billing_series.call_args.kwargs["payload"]
    assert payload["customers"] == [{"customer_code": "999", "customer_store": "01"}]


def test_outbound_invoices_bff_allows_outside_portfolio() -> None:
    """Conta detalhe: accounts.view basta — sem ensure_allows de membership."""
    gateway = MagicMock()
    gateway.list_customer_outbound_invoices.return_value = {
        "data": {"items": [], "pagination": {"page": 1, "page_size": 20, "total": 0}}
    }

    request = _request("/customers/999/01/outbound-invoices")
    request.state.user = _User(["commercial.accounts.view"])

    with patch.object(
        customer_routes,
        "build_delpi_commercial_gateway",
        return_value=gateway,
    ):
        response = customer_routes.list_commercial_customer_outbound_invoices(
            request,
            customer_code="999",
            customer_store="01",
        )

    assert response.status_code == 200
    gateway.list_customer_outbound_invoices.assert_called_once()


def test_get_outbound_invoice_bff_returns_invoice() -> None:
    gateway = MagicMock()
    gateway.get_outbound_invoice.return_value = {
        "data": {
            "key": "01|000123|1",
            "branch": "01",
            "invoice_number": "000123",
            "invoice_series": "1",
            "customer_code": "999",
            "customer_store": "01",
            "items": [],
        }
    }

    request = _request("/customers/999/01/outbound-invoices/01/000123/1")
    request.state.user = _User(["commercial.accounts.view"])

    with patch.object(
        customer_routes,
        "build_delpi_commercial_gateway",
        return_value=gateway,
    ):
        response = customer_routes.get_commercial_customer_outbound_invoice(
            request,
            customer_code="999",
            customer_store="01",
            branch="01",
            invoice_number="000123",
            invoice_series="1",
        )

    assert response.status_code == 200
    gateway.get_outbound_invoice.assert_called_once_with(
        branch="01",
        invoice_number="000123",
        invoice_series="1",
    )


def test_get_outbound_invoice_bff_rejects_customer_mismatch() -> None:
    gateway = MagicMock()
    gateway.get_outbound_invoice.return_value = {
        "data": {
            "customer_code": "OTHER",
            "customer_store": "01",
            "items": [],
        }
    }
    request = _request("/customers/999/01/outbound-invoices/01/000123/1")
    request.state.user = _User(["commercial.accounts.view"])

    with patch.object(
        customer_routes,
        "build_delpi_commercial_gateway",
        return_value=gateway,
    ):
        response = customer_routes.get_commercial_customer_outbound_invoice(
            request,
            customer_code="999",
            customer_store="01",
            branch="01",
            invoice_number="000123",
            invoice_series="1",
        )

    assert response.status_code == 404


def test_customer_open_orders_bff_allows_outside_portfolio() -> None:
    """Conta detalhe: pedidos por cliente sem dump global nem membership."""
    gateway = MagicMock()
    gateway.list_open_orders_by_customer.return_value = {
        "data": {"items": [{"pedido": "1"}], "summary": {"total_linhas": 1}}
    }

    request = _request("/customers/000001/06/open-orders")
    request.state.user = _User(["commercial.accounts.view"])

    with patch.object(
        customer_routes,
        "build_delpi_commercial_gateway",
        return_value=gateway,
    ):
        response = customer_routes.list_commercial_customer_open_orders(
            request,
            customer_code="000001",
            customer_store="06",
        )

    assert response.status_code == 200
    gateway.list_open_orders_by_customer.assert_called_once_with(
        customer_code="000001",
        customer_store="06",
    )
