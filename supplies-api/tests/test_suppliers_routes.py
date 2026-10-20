"""Suppliers BFF routes — AuthZ, S2S gateway usage, LGPD projection, errors."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.application.services import suppliers_dto
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


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
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="user-jwt",
    )


def _envelope(items, total=1):
    return {
        "success": True,
        "data": {
            "items": items,
            "page": 1,
            "page_size": 20,
            "total": total,
            "total_pages": 1,
            "pagination": {},
        },
        "meta": {"operation_id": "list_supplies_suppliers"},
    }


_ITEM = {
    "supplier_id": "00000101",
    "supplier_code": "000001",
    "supplier_store": "01",
    "supplier_name": "ACME",
    "supplier_short_name": "ACME",
    "tax_id": "12345678901",
    "state": "SC",
    "blocked": False,
}


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


class TestList:
    def test_missing_bearer_401(self, client):
        assert client.get("/suppliers").status_code == 401

    def test_no_access_403(self, client):
        v, r = _auth(permissions={"supplies.manage"})
        with v, r:
            assert client.get(
                "/suppliers", headers={"Authorization": "Bearer t"}
            ).status_code == 403

    def test_list_projects_and_masks_cpf(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = _envelope([_ITEM])
            resp = client.get(
                "/suppliers?query=acme&page=2",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        item = resp.get_json()["items"][0]
        assert item["tax_id"] == "***********"
        assert item["tax_id_masked"] is True
        assert item["supplier_id"] == "00000101"
        gw.get.assert_called_once_with(
            "/supplies/suppliers",
            access_token="user-jwt",
            params={"query": "acme", "page": "2"},
        )

    def test_cnpj_not_masked(self, client):
        v, r = _auth()
        cnpj_item = dict(_ITEM, tax_id="12345678000190")
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = _envelope([cnpj_item])
            resp = client.get("/suppliers", headers={"Authorization": "Bearer t"})
        item = resp.get_json()["items"][0]
        assert item["tax_id"] == "12345678000190"
        assert item["tax_id_masked"] is False

    def test_upstream_5xx_maps_502(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError("boom", status_code=500)
            assert client.get(
                "/suppliers", headers={"Authorization": "Bearer t"}
            ).status_code == 502

    def test_upstream_403_propagates_s2s_denial_code(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "denied", status_code=403, code="S2S_SCOPE_DENIED"
            )
            resp = client.get("/suppliers", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "S2S_SCOPE_DENIED"

    def test_upstream_403_without_code_maps_upstream_forbidden(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "denied", status_code=403
            )
            resp = client.get("/suppliers", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "upstream_forbidden"


class TestDetail:
    def test_detail_composes_supplier_id(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = {
                "success": True,
                "data": {
                    "fornecedor": {
                        "supplier_name": "ACME",
                        "tax_id": "12345678901",
                        "email": "x@y.z",
                    }
                },
            }
            resp = client.get(
                "/suppliers/1/1", headers={"Authorization": "Bearer t"}
            )
        assert resp.status_code == 200
        gw.get.assert_called_once_with(
            "/integrations/protheus/suppliers/00000101",
            access_token="user-jwt",
        )
        body = resp.get_json()
        assert body["sections"]["identification"]["supplier_name"] == "ACME"
        assert body["tax_id_masked"] is True

    def test_detail_404(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError("nf", status_code=404)
            assert client.get(
                "/suppliers/999999/01", headers={"Authorization": "Bearer t"}
            ).status_code == 404

    def test_detail_invalid_id_422(self, client):
        v, r = _auth()
        with v, r:
            assert client.get(
                "/suppliers/123456789/1", headers={"Authorization": "Bearer t"}
            ).status_code == 422


class TestWrite:
    def test_post_rejects_codusr(self, client):
        v, r = _auth()
        with v, r:
            resp = client.post(
                "/suppliers",
                json={"fornecedor": {"supplier_name": "X", "codusr": "000161"}},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 422

    def test_post_filters_to_allowlist(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.post.return_value = {
                "success": True,
                "data": {"creation_confirmed": False},
            }
            resp = client.post(
                "/suppliers",
                json={
                    "fornecedor": {
                        "supplier_name": "X",
                        "evil_field": "drop",
                        "supplier_store": "01",
                    }
                },
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["acknowledged"] is True
        assert body["persistence_proven"] is False
        sent = gw.post.call_args.kwargs["json_body"]["fornecedor"]
        assert sent == {"supplier_name": "X", "supplier_store": "01"}

    def test_put_allowlist_two_fields(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.put.return_value = {
                "success": True,
                "data": {"update_acknowledged": True, "persistence_proven": False},
            }
            resp = client.put(
                "/suppliers/000001/01",
                json={
                    "fornecedor": {
                        "supplier_name": "N1",
                        "supplier_short_name": "N2",
                    }
                },
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        sent = gw.put.call_args.kwargs["json_body"]["fornecedor"]
        assert sent == {"supplier_name": "N1", "supplier_short_name": "N2"}
        assert resp.get_json()["persistence_proven"] is False

    def test_put_rejects_non_allowlisted(self, client):
        v, r = _auth()
        with v, r:
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {"email": "a@b.c"}},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 422

    def test_post_gate_disabled_reports_write_disabled(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.post.side_effect = DelpiApiGatewayError(
                "gated",
                status_code=503,
                code="PROTHEUS_SUPPLIER_CREATE_DISABLED",
            )
            resp = client.post(
                "/suppliers",
                json={"fornecedor": {"supplier_name": "X"}},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 503
        assert resp.get_json()["outcome"] == "write_disabled"

    def test_put_timeout_indeterminate(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.put.side_effect = DelpiApiGatewayError("api-delpi timeout")
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {"supplier_name": "N"}},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 504
        assert resp.get_json()["outcome"] == "indeterminate"
