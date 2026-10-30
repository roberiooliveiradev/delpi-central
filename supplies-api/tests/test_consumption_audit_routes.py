"""Consumption-audit BFF route — AuthZ Core-first, unit scope, S2S upstream.

``GET /consumption-audit/orders/{production_order}?unit=01|02`` requires the
effective ``supplies.access`` permission (``supplies.manage`` alone never
reads) and forwards to api-delpi exclusively through ``DelpiS2SApiGateway``
— the shared legacy token is never used and no Protheus rule lives here.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


OP = "24884201006"


@pytest.fixture()
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def _identity():
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="auditor@delpi.com.br",
        name="Auditor",
    )


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="auditor@delpi.com.br",
        name="Auditor",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="user-jwt",
    )


def _auth(*, permissions={"supplies.access"}):
    validate = patch(
        "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate",
        return_value=_identity(),
    )
    resolve = patch(
        "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user",
        return_value=_user(permissions=permissions),
    )
    return validate, resolve


def _producer_payload():
    return {
        "success": True,
        "data": {
            "branch": "01",
            "production_order": OP,
            "order": {
                "order_number": "248842",
                "order_item": "01",
                "order_sequence": "006",
                "product_code": "50226108",
                "produced_quantity_basis": "stock_receipt",
            },
            "operations": [],
            "quality": {"status": "partial", "warnings": []},
        },
        "meta": {"operation_id": "get_consumption_audit_order"},
    }


_GW = "app.interfaces.http.routes.consumption_audit_routes._GATEWAY"


class TestAuthz:
    def test_missing_bearer_401(self, client):
        resp = client.get(f"/consumption-audit/orders/{OP}?unit=01")
        assert resp.status_code == 401

    def test_manage_only_without_access_403(self, client):
        v, r = _auth(permissions={"supplies.manage"})
        with v, r, patch(_GW) as gw:
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403
        gw.get.assert_not_called()

    def test_access_permission_reaches_gateway(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.return_value = _producer_payload()
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200

    def test_missing_unit_is_403(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            resp = client.get(
                f"/consumption-audit/orders/{OP}",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403
        gw.get.assert_not_called()

    def test_unit_out_of_scope_is_403(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=03",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403
        gw.get.assert_not_called()


class TestValidation:
    def test_malformed_production_order_is_422(self, client):
        v, r = _auth()
        for bad in ("2488420100", "248842010061", "24884201*06"):
            with v, r, patch(_GW) as gw:
                resp = client.get(
                    f"/consumption-audit/orders/{bad}?unit=01",
                    headers={"Authorization": "Bearer t"},
                )
            assert resp.status_code == 422
            assert resp.get_json()["code"] == "invalid_request"
            gw.get.assert_not_called()


class TestUpstream:
    def test_happy_path_forwards_branch_and_projects_data(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.return_value = _producer_payload()
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["order"]["product_code"] == "50226108"
        assert body["order"]["produced_quantity_basis"] == "stock_receipt"
        gw.get.assert_called_once_with(
            f"/supplies/consumption-audit/orders/{OP}",
            access_token="user-jwt",
            params={"branch": "01"},
        )

    def test_upstream_404_maps_not_found(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "missing", status_code=404
            )
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 404
        assert resp.get_json()["code"] == "not_found"

    def test_upstream_403_propagates_s2s_denial_code(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "denied", status_code=403, code="S2S_SCOPE_DENIED"
            )
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "S2S_SCOPE_DENIED"

    def test_upstream_timeout_maps_504(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.side_effect = DelpiApiGatewayError("timeout")
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 504
        assert resp.get_json()["code"] == "upstream_unreachable"

    def test_upstream_5xx_maps_502_sanitized(self, client):
        v, r = _auth()
        with v, r, patch(_GW) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "boom", status_code=500
            )
            resp = client.get(
                f"/consumption-audit/orders/{OP}?unit=01",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 502
        assert resp.get_json()["detail"] == "api-delpi unavailable"

    def test_malformed_upstream_payload_is_502(self, client):
        v, r = _auth()
        for bad_payload in (
            {"success": True, "data": None},
            {"success": True, "data": {"operations": []}},  # sem "order"
            ["not-a-dict"],
        ):
            with v, r, patch(_GW) as gw:
                gw.get.return_value = bad_payload
                resp = client.get(
                    f"/consumption-audit/orders/{OP}?unit=01",
                    headers={"Authorization": "Bearer t"},
                )
            assert resp.status_code == 502, bad_payload
            assert resp.get_json()["code"] == "bad_gateway"
