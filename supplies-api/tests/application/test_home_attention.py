from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import patch

from app.application.services.home_attention_service import HomeAttentionService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGatewayError,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


class FakeDelpiReads:
    def __init__(self, *, fail: set[str] | None = None) -> None:
        self.fail = fail or set()

    def get_purchase_orders(self, **kwargs: Any) -> dict[str, Any]:
        if "purchase_orders" in self.fail:
            raise DelpiApiGatewayError("boom", status_code=502)
        return {
            "items": [
                {
                    "order_number": "100001",
                    "order_item": "10",
                    "supplier_name": "Fornecedor A",
                    "expected_delivery_date": "2026-10-05",
                }
            ],
            "summary": {"total_lines": 30, "late_lines": 2, "on_time_lines": 27},
            "total": 2,
        }

    def get_purchase_order_otd_panel(self, **kwargs: Any) -> dict[str, Any]:
        if "late_deliveries" in self.fail:
            raise DelpiApiGatewayError("boom", status_code=502)
        return {
            "summary": {
                "total_lines": 10,
                "on_time_lines": 7,
                "late_lines": 3,
                "late_percentage": 30.0,
            },
            "lines": {
                "items": [
                    {
                        "order_number": "200001",
                        "order_item": "5",
                        "supplier_name": "Fornecedor B",
                        "supplier_short_name": "Forn. B",
                        "days_diff": -4,
                    }
                ],
                "total": 3,
            },
        }

    def get_safety_stock_summary(self, **kwargs: Any) -> dict[str, Any]:
        if "safety_stock" in self.fail:
            raise DelpiApiGatewayError("boom", status_code=502)
        return {"below_safety_stock": 2}

    def get_safety_stock_items(self, **kwargs: Any) -> dict[str, Any]:
        if "safety_stock" in self.fail:
            raise DelpiApiGatewayError("boom", status_code=502)
        return {
            "items": [
                {
                    "product_code": "30100001",
                    "product_description": "Resina X",
                    "available_stock": 2.0,
                    "safety_stock": 10.0,
                }
            ]
        }


class FakePurchaseRequests:
    OPEN_STAGES = ()

    def __init__(self, *, fail: bool = False, buckets: dict | None = None) -> None:
        self.fail = fail
        self.buckets = buckets or {"ordering": 2, "receiving": 1, "completed": 5}
        self.list_calls: list[dict[str, Any]] = []

    def get_summary(self, **kwargs: Any) -> dict[str, Any]:
        if self.fail:
            raise PurchaseRequestsGatewayError("boom", status_code=502)
        return {
            "data": {
                "total_requests": 8,
                "total_items": 10,
                "buckets": self.buckets,
            }
        }

    def list_purchase_requests(self, **kwargs: Any) -> dict[str, Any]:
        if self.fail:
            raise PurchaseRequestsGatewayError("boom", status_code=502)
        params = kwargs.get("params") or {}
        self.list_calls.append(params)
        return {
            "data": {
                "items": [
                    {
                        "request_number": "000123",
                        "branch": params.get("branch", ["01"])[0],
                        "requester": {"name": "Fulano"},
                    }
                    for _ in range(5)  # producer must be capped at 3 by us
                ]
            }
        }


def _service(
    *,
    delpi: FakeDelpiReads | None = None,
    prs: FakePurchaseRequests | None = None,
) -> HomeAttentionService:
    return HomeAttentionService(
        delpi_reads=delpi or FakeDelpiReads(),
        purchase_requests=prs or FakePurchaseRequests(),
        today_provider=lambda: date(2026, 10, 23),
    )


def test_compose_access_user_gets_real_cards():
    result = _service().compose(_user(permissions={"supplies.access"}))
    ids = {card["id"] for card in result["cards"]}
    assert ids == {
        "purchase_requests_ordering",
        "purchase_requests_receiving",
        "purchase_orders_late",
        "late_deliveries",
        "safety_stock_below",
    }
    assert result["partialFailures"] == []


def test_compose_counts_and_units():
    result = _service().compose(_user(permissions={"supplies.access"}))
    by_id = {card["id"]: card for card in result["cards"]}
    # PR buckets are header counts.
    assert by_id["purchase_requests_ordering"]["count"] == 2
    assert by_id["purchase_requests_ordering"]["countUnit"] == "solicitações"
    assert by_id["purchase_requests_receiving"]["count"] == 1
    # PO late lines.
    assert by_id["purchase_orders_late"]["count"] == 2
    assert by_id["purchase_orders_late"]["countUnit"] == "linhas"
    # Late deliveries summed across the two allowed units (3 + 3).
    assert by_id["late_deliveries"]["count"] == 6
    # Safety stock summed across units (2 + 2).
    assert by_id["safety_stock_below"]["count"] == 4
    assert by_id["safety_stock_below"]["countUnit"] == "itens"


def test_compose_targets_and_previews():
    prs = FakePurchaseRequests()
    result = _service(prs=prs).compose(_user(permissions={"supplies.access"}))
    by_id = {card["id"]: card for card in result["cards"]}

    ordering = by_id["purchase_requests_ordering"]
    assert ordering["target"] == {
        "kind": "view",
        "viewId": "purchase_requests",
        "query": "overall_stage=awaiting_order&overall_stage=partially_ordered",
    }
    assert len(ordering["preview"]) == 3  # capped, never the raw 5
    assert ordering["preview"][0]["label"] == "SC 000123"

    po = by_id["purchase_orders_late"]
    assert po["target"]["viewId"] == "purchase_orders"
    assert po["target"]["query"] == "late_only=true"
    assert po["preview"][0]["label"] == "PC 100001/10"

    deliveries = by_id["late_deliveries"]
    assert deliveries["target"]["viewId"] == "deliveries"
    assert deliveries["target"]["query"] == "status=late"
    assert deliveries["preview"][0]["detail"] == "4 dias de atraso"

    safety = by_id["safety_stock_below"]
    assert safety["target"] is None  # user lacks estoque-seguranca.access

    # Preview list calls used the owner's stage filter param.
    stages_seen = [call.get("overall_stage") for call in prs.list_calls]
    assert ["awaiting_order", "partially_ordered"] in stages_seen
    assert ["ordered", "awaiting_receipt", "partially_received"] in stages_seen


def test_safety_stock_target_when_user_has_app_access():
    user = _user(permissions={"supplies.access", "estoque-seguranca.access"})
    result = _service().compose(user)
    safety = next(c for c in result["cards"] if c["id"] == "safety_stock_below")
    assert safety["target"] == {"kind": "href", "href": "/apps/estoque-seguranca"}


def test_compose_zero_counts_emit_empty():
    prs = FakePurchaseRequests(buckets={"ordering": 0, "receiving": 0, "completed": 5})

    class EmptyDelpi(FakeDelpiReads):
        def get_purchase_orders(self, **kwargs):
            return {"items": [], "summary": {"late_lines": 0}}

        def get_purchase_order_otd_panel(self, **kwargs):
            return {"summary": {"late_lines": 0}, "lines": {"items": []}}

        def get_safety_stock_summary(self, **kwargs):
            return {"below_safety_stock": 0}

    result = _service(delpi=EmptyDelpi(), prs=prs).compose(
        _user(permissions={"supplies.access"})
    )
    assert result["cards"] == []
    assert result["partialFailures"] == []
    # No preview calls when counts are zero.
    assert prs.list_calls == []


def test_compose_source_failure_is_unavailable_not_zero():
    delpi = FakeDelpiReads(fail={"late_deliveries"})
    result = _service(delpi=delpi).compose(_user(permissions={"supplies.access"}))
    by_id = {card["id"]: card for card in result["cards"]}
    card = by_id["late_deliveries"]
    assert card["status"] == "unavailable"
    assert card["count"] is None
    assert card["target"] is None
    assert {f["source"] for f in result["partialFailures"]} == {"late_deliveries"}
    # Independent sources still available.
    assert by_id["purchase_orders_late"]["count"] == 2


def test_compose_purchase_requests_failure_hides_both_cards():
    prs = FakePurchaseRequests(fail=True)
    result = _service(prs=prs).compose(_user(permissions={"supplies.access"}))
    by_id = {card["id"]: card for card in result["cards"]}
    assert by_id["purchase_requests_ordering"]["status"] == "unavailable"
    assert by_id["purchase_requests_receiving"]["status"] == "unavailable"
    assert {f["source"] for f in result["partialFailures"]} == {"purchase_requests"}
    assert by_id["safety_stock_below"]["status"] == "available"


def test_compose_preview_failure_keeps_count():
    class PreviewFailPR(FakePurchaseRequests):
        def list_purchase_requests(self, **kwargs):
            raise PurchaseRequestsGatewayError("preview down")

    result = _service(prs=PreviewFailPR()).compose(
        _user(permissions={"supplies.access"})
    )
    ordering = next(
        c for c in result["cards"] if c["id"] == "purchase_requests_ordering"
    )
    assert ordering["status"] == "available"
    assert ordering["count"] == 2
    assert ordering["preview"] == []


def test_compose_old_portal_code_omits_cards():
    result = _service().compose(_user(permissions={"supplies.portal.access"}))
    assert result["cards"] == []
    assert result["partialFailures"] == []


def test_compose_superadmin_gets_all_units():
    result = _service().compose(_user(permissions=set(), is_superadmin=True))
    ids = {card["id"] for card in result["cards"]}
    assert "late_deliveries" in ids
    assert "safety_stock_below" in ids
    safety = next(c for c in result["cards"] if c["id"] == "safety_stock_below")
    assert safety["target"] == {"kind": "href", "href": "/apps/estoque-seguranca"}


def _stubbed_service():
    return _service()


@patch("app.interfaces.http.routes.home_routes.HomeAttentionService")
@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_positive(mock_resolve, mock_validate, mock_service):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    mock_service.return_value = _stubbed_service()
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "cards" in body
    assert body["partialFailures"] == []
    ids = {card["id"] for card in body["cards"]}
    assert "purchase_orders_late" in ids
    assert "administration" not in ids
    assert "overview" not in ids


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_old_code_forbidden(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_home_attention_forbidden_without_portal(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.analytics.access"})
    client = create_app().test_client()
    response = client.get(
        "/home/attention",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
def test_http_home_attention_requires_auth(mock_validate):
    mock_validate.side_effect = Exception("invalid")
    client = create_app().test_client()
    response = client.get("/home/attention")
    assert response.status_code in (401, 403)
