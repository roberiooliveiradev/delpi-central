from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    ResolveCommercialCustomerScopeService,
)
from commercial_app.application.use_cases.preview_interaction_entity import (
    PreviewInteractionEntityUseCase,
)
from commercial_app.interface.http.routes import interaction_room_routes
from tests.test_interaction_mention_suggest_crm import _Portfolios, _portfolio


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub


class _Directory:
    def lookup_directory_users(self, user_ids):
        if "u2" in user_ids:
            return {"u2": {"id": "u2", "name": "Ana", "email": "ana@delpi"}}
        return {}


class _Gateway:
    def search_active_customers(self, *, params=None):
        return {
            "data": {
                "items": [
                    {"code": "0001", "store": "01", "name": "WEG"},
                    {"code": "9999", "store": "01", "name": "Fora"},
                ]
            }
        }

    def list_open_orders(self, *, params=None):
        return {
            "data": {
                "items": [
                    {
                        "filial": "01",
                        "pedido": "102942",
                        "codigo_cadastro": "0001",
                        "loja_cadastro": "01",
                        "nome_cliente": "WEG",
                    },
                    {
                        "filial": "01",
                        "pedido": "1",
                        "codigo_cadastro": "9999",
                        "loja_cadastro": "01",
                        "nome_cliente": "Fora",
                    },
                ]
            }
        }

    def get_product(self, path, *, params=None):
        if path.endswith("/factory-status"):
            return {"data": {"product_code": "90AAAA01", "description": "Tampa", "um": "PC"}}
        raise RuntimeError("not found")

    def get_production(self, path, *, params=None):
        return {"data": {"op": "00118901001", "branch": "01"}}

    def get_commercial_analytics(self, path, *, params=None):
        if path == "/proposals":
            return {
                "data": {
                    "items": [
                        {
                            "proposal_number": "OV-1",
                            "customer_name": "WEG",
                            "customer_code": "0001",
                            "customer_store": "01",
                        },
                        {
                            "proposal_number": "OV-9",
                            "customer_code": "9999",
                            "customer_store": "01",
                        },
                    ]
                }
            }
        if path == "/sales-order-otd/panel":
            return {
                "data": {
                    "items": [
                        {
                            "branch": "01",
                            "order_number": "102942",
                            "line_item": "01",
                            "customer_code": "0001",
                            "customer_store": "01",
                        }
                    ]
                }
            }
        return {"data": {"items": []}}

    def list_customer_outbound_invoices(self, *, customer_code, customer_store, params=None):
        return {"data": {"items": []}}

    def get_outbound_invoice(self, *, branch, invoice_number, invoice_series):
        return {
            "data": {
                "invoice_number": invoice_number,
                "series": invoice_series,
                "filial": branch,
                "customer_code": "0001",
                "customer_store": "01",
            }
        }


def _uc(gateway=None) -> PreviewInteractionEntityUseCase:
    repo = _Portfolios([_portfolio()])
    return PreviewInteractionEntityUseCase(
        _Directory(),
        portfolios=repo,
        scope=ResolveCommercialCustomerScopeService(repo),
        gateway=gateway or _Gateway(),
    )


def _request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/interaction-rooms/entity-preview",
        "raw_path": b"/interaction-rooms/entity-preview",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_preview_user_ok() -> None:
    card = _uc().preview(kind="user", ref={"user_id": "u2"}, actor_user_id="u1")
    assert card["accessible"] is True
    assert card["label"] == "Ana"
    assert card["hrefStrategy"] == "user_profile"


def test_preview_customer_out_of_scope_is_opaque() -> None:
    card = _uc().preview(
        kind="customer",
        ref={"customer_code": "9999", "customer_store": "01"},
        actor_user_id="u1",
    )
    assert card["accessible"] is False
    assert "Sem acesso" in card["label"]
    assert card["fields"] == {}


def test_preview_customer_in_scope() -> None:
    card = _uc().preview(
        kind="customer",
        ref={"customer_code": "0001", "customer_store": "01"},
        actor_user_id="u1",
    )
    assert card["accessible"] is True
    assert card["label"] == "WEG"


def test_preview_order_and_product_and_invoice() -> None:
    uc = _uc()
    order = uc.preview(
        kind="order",
        ref={"branch": "01", "order": "102942"},
        actor_user_id="u1",
    )
    assert order["accessible"] is True
    product = uc.preview(
        kind="product",
        ref={"product_code": "90AAAA01"},
        actor_user_id="u1",
    )
    assert product["accessible"] is True
    assert product["fields"].get("um") == "PC"
    invoice = uc.preview(
        kind="invoice",
        ref={"branch": "01", "invoice": "000123", "series": "1"},
        actor_user_id="u1",
    )
    assert invoice["accessible"] is True


def test_preview_opportunity_out_of_scope_is_opaque() -> None:
    card = _uc().preview(
        kind="opportunity",
        ref={"proposal_number": "OV-9"},
        actor_user_id="u1",
    )
    assert card["accessible"] is False


def test_preview_gateway_error_is_opaque() -> None:
    class Boom(_Gateway):
        def get_product(self, path, *, params=None):
            raise RuntimeError("down")

    card = _uc(Boom()).preview(
        kind="product",
        ref={"product_code": "90AAAA01"},
        actor_user_id="u1",
    )
    assert card["accessible"] is False


def test_preview_unknown_kind_raises() -> None:
    with pytest.raises(ValueError):
        _uc().preview(kind="spaceship", ref={}, actor_user_id="u1")


def test_preview_task_kind_without_preview_is_opaque() -> None:
    card = _uc().preview(
        kind="task",
        ref={"task_id": "12c22442-c394-42e3-9998-d256928829cc"},
        actor_user_id="u1",
    )
    assert card["accessible"] is False
    assert card["kind"] == "task"
    assert card["fields"] == {}


def test_preview_route_opaque_200(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request()
    request.state.user = _User(["commercial.access"])
    fake_uc = MagicMock()
    fake_uc.preview.return_value = {
        "kind": "order",
        "accessible": False,
        "label": "Sem acesso a este registro.",
        "subtitle": "",
        "hrefStrategy": "order_detail",
        "ref": {"branch": "01", "order": "1"},
        "fields": {},
    }
    monkeypatch.setattr(
        interaction_room_routes,
        "build_preview_interaction_entity_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.preview_interaction_entity(
        request,
        kind="order",
        ref=json.dumps({"branch": "01", "order": "1"}),
    )
    assert response.status_code == 200
    assert b"preview_interaction_entity" in response.body
    assert b"Sem acesso" in response.body
