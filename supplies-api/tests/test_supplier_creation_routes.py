"""Supplier creation preview route — AuthZ, validation, errors (X4.UX-R1.S1)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.application.services.supplier_enrichment.contracts import (
    RegistryRateLimitedError,
    RegistryTaxIdNotFoundError,
)
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.supplier_enrichment.models import ExternalRegistrySnapshot

TAX_ID = "00000000000191"


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


def _user(*, permissions: set[str]) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
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


def _snapshot():
    return ExternalRegistrySnapshot(
        tax_id=TAX_ID,
        source_id="brasilapi-cnpj-v1",
        retrieved_at="2026-10-23T12:00:00Z",
        fields={"company.legal_name": "BANCO DO BRASIL SA"},
    )


def _patch_backends(registry=None, dup=None, limiter=None):
    registry = registry or MagicMock(fetch=MagicMock(return_value=_snapshot()))
    dup = dup or MagicMock(
        search_by_tax_id=MagicMock(return_value=([], 0))
    )
    limiter = limiter or MagicMock()
    return (
        patch(
            "app.interfaces.http.routes.supplier_creation_routes.company_registry_provider",
            return_value=registry,
        ),
        patch(
            "app.interfaces.http.routes.supplier_creation_routes.DelpiSupplierDuplicateSearch",
            return_value=dup,
        ),
        patch(
            "app.interfaces.http.routes.supplier_creation_routes.registry_rate_limiter",
            return_value=limiter,
        ),
    )


def _post(client, body=None):
    return client.post(
        "/suppliers/creation-preview",
        json=body if body is not None else {"tax_id": TAX_ID},
        headers={"Authorization": "Bearer t"},
    )


class TestAuthz:
    def test_missing_bearer_401(self, client):
        assert client.post("/suppliers/creation-preview", json={}).status_code == 401

    def test_no_capability_403(self, client):
        v, r = _auth(permissions={"supplies.manage"})
        with v, r:
            assert _post(client).status_code == 403


class TestRequestValidation:
    def test_invalid_check_digits_422(self, client):
        v, r = _auth()
        with v, r:
            resp = _post(client, {"tax_id": "12345678000196"})
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "invalid_request"

    def test_unexpected_fields_422(self, client):
        v, r = _auth()
        with v, r:
            resp = _post(client, {"tax_id": TAX_ID, "actor": "x"})
        assert resp.status_code == 422

    def test_server_owned_fields_422(self, client):
        v, r = _auth()
        with v, r:
            resp = _post(client, {"tax_id": TAX_ID, "unit_context": "01"})
        assert resp.status_code == 422

    def test_non_object_body_422(self, client):
        v, r = _auth()
        with v, r:
            resp = client.post(
                "/suppliers/creation-preview",
                data='"text"',
                content_type="application/json",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 422


class TestPreview:
    def test_success_response(self, client):
        v, r = _auth()
        reg_patch, dup_patch, lim_patch = _patch_backends()
        with v, r, reg_patch, dup_patch, lim_patch:
            resp = _post(client)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["tax_id_masked"] == "00.***.***/0001-**"
        assert body["person_type"] == "J"
        assert body["write_enabled"] is False
        assert body["duplicate_check"]["status"] == "CLEAR"
        assert body["suggestions"][0]["field_key"] == "supplier_name"
        assert body["suggestions"][0]["source"]["provider_id"] == (
            "brasilapi-cnpj-v1"
        )

    def test_masked_tax_id_normalized_before_fetch(self, client):
        registry = MagicMock(fetch=MagicMock(return_value=_snapshot()))
        dup = MagicMock(search_by_tax_id=MagicMock(return_value=([], 0)))
        reg_patch, dup_patch, lim_patch = _patch_backends(registry, dup)
        v, r = _auth()
        with v, r, reg_patch, dup_patch, lim_patch:
            resp = _post(client, {"tax_id": "00.000.000/0001-91"})
        assert resp.status_code == 200
        registry.fetch.assert_called_once_with(TAX_ID)
        dup.search_by_tax_id.assert_called_once_with(
            TAX_ID, access_token="user-jwt"
        )

    def test_duplicate_possible_match(self, client):
        dup = MagicMock(
            search_by_tax_id=MagicMock(
                return_value=(
                    [
                        {
                            "supplier_code": "000001",
                            "supplier_store": "01",
                            "supplier_name": "EXISTENTE",
                            "state": "SC",
                            "blocked": False,
                        }
                    ],
                    1,
                )
            )
        )
        reg_patch, dup_patch, lim_patch = _patch_backends(dup=dup)
        v, r = _auth()
        with v, r, reg_patch, dup_patch, lim_patch:
            body = _post(client).get_json()
        assert body["duplicate_check"]["status"] == "POSSIBLE_MATCH"
        assert body["duplicate_check"]["matches"][0]["supplier_code"] == "000001"

    def test_cnpj_not_found_404(self, client):
        registry = MagicMock(
            fetch=MagicMock(
                side_effect=RegistryTaxIdNotFoundError("CNPJ not found")
            )
        )
        reg_patch, dup_patch, lim_patch = _patch_backends(registry)
        v, r = _auth()
        with v, r, reg_patch, dup_patch, lim_patch:
            resp = _post(client)
        assert resp.status_code == 404
        assert resp.get_json()["code"] == "ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND"

    def test_rate_limited_429_retry_after(self, client):
        registry = MagicMock(
            fetch=MagicMock(
                side_effect=RegistryRateLimitedError("limited", retry_after=30)
            )
        )
        reg_patch, dup_patch, lim_patch = _patch_backends(registry)
        v, r = _auth()
        with v, r, reg_patch, dup_patch, lim_patch:
            resp = _post(client)
        assert resp.status_code == 429
        assert resp.headers["Retry-After"] == "30"


class TestNoSideEffects:
    def test_route_performs_no_writes(self, client):
        # The preview must never touch POST/PUT on the api-delpi gateway nor
        # persist anything: only ``search_by_tax_id`` (GET) is invoked.
        dup = MagicMock(search_by_tax_id=MagicMock(return_value=([], 0)))
        registry = MagicMock(fetch=MagicMock(return_value=_snapshot()))
        reg_patch, dup_patch, lim_patch = _patch_backends(registry, dup)
        v, r = _auth()
        with v, r, reg_patch, dup_patch, lim_patch, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as list_gw:
            resp = _post(client)
        assert resp.status_code == 200
        list_gw.post.assert_not_called()
        list_gw.put.assert_not_called()
