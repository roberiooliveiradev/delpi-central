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

    def test_detail_projects_e3_sections(self, client):
        """E3 promoted fields surface in the curated detail sections."""
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = {
                "success": True,
                "data": {
                    "fornecedor": {
                        "supplier_name": "ACME",
                        "address_number": "385",
                        "cnae_code": "6201501",
                        "carrier_code": "000001",
                        "bank_account": "999",  # sensitive — never projected
                        "credit_limit_amount": "10",  # accumulator — never projected
                    }
                },
            }
            resp = client.get(
                "/suppliers/1/1", headers={"Authorization": "Bearer t"}
            )
        body = resp.get_json()
        assert body["sections"]["address"]["address_number"] == "385"
        assert body["sections"]["fiscal"]["cnae_code"] == "6201501"
        assert body["sections"]["purchasing"]["carrier_code"] == "000001"
        assert "bank_account" not in str(body)
        assert "credit_limit_amount" not in str(body)


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

    def test_put_extended_cadastral_fields(self, client):
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
                        "address": "RUA X",
                        "postal_code": "89120000",
                        "email": "a@b.c",
                        "state_registration": "123",
                        "payment_condition_code": "010",
                        "rohs_indicator": "N",
                    }
                },
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        sent = gw.put.call_args.kwargs["json_body"]["fornecedor"]
        assert sent == {
            "address": "RUA X",
            "postal_code": "89120000",
            "email": "a@b.c",
            "state_registration": "123",
            "payment_condition_code": "010",
            "rohs_indicator": "N",
        }

    def test_put_rejects_protected_fields(self, client):
        v, r = _auth()
        for key in ("tax_id", "supplier_code", "supplier_store"):
            with v, r:
                resp = client.put(
                    "/suppliers/000001/01",
                    json={"fornecedor": {key: "01"}},
                    headers={"Authorization": "Bearer t"},
                )
            assert resp.status_code == 422, key

    def test_put_rejects_codusr_and_unknown_fields(self, client):
        v, r = _auth()
        with v, r:
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {"codusr": "000161", "supplier_name": "X"}},
                headers={"Authorization": "Bearer t"},
            )
            assert resp.status_code == 422
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {"a2_filial": "01"}},
                headers={"Authorization": "Bearer t"},
            )
            assert resp.status_code == 422

    def test_put_rejects_empty_body(self, client):
        v, r = _auth()
        with v, r:
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {}},
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

    # --- X4.FIELDS.E3 — promoted fields pass POST, stay out of PUT -------

    def test_post_forwards_e3_promoted_fields(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.post.return_value = {"success": True, "data": {}}
            resp = client.post(
                "/suppliers",
                json={
                    "fornecedor": {
                        "supplier_name": "X",
                        "supplier_store": "01",
                        "address_number": "385",
                        "cnae_code": "6201501",
                        "linked_customer_code": "000123",
                        "person_category": "PJ",  # NOT promoted — dropped
                    }
                },
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        sent = gw.post.call_args.kwargs["json_body"]["fornecedor"]
        assert sent == {
            "supplier_name": "X",
            "supplier_store": "01",
            "address_number": "385",
            "cnae_code": "6201501",
            "linked_customer_code": "000123",
        }

    def test_put_forwards_e5_homologated_fields(self, client):
        """E5 proved PUT persistence — BFF forwards the homologated set."""
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.put.return_value = {"success": True, "data": {}}
            resp = client.put(
                "/suppliers/000001/01",
                json={
                    "fornecedor": {
                        "address_number": "1024",
                        "cnae_code": "6202300",
                        "carrier_code": "000123",
                        "swift_code": "BRASBRRJXXX",
                    }
                },
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        sent = gw.put.call_args.kwargs["json_body"]["fornecedor"]
        assert sent == {
            "address_number": "1024",
            "cnae_code": "6202300",
            "carrier_code": "000123",
            "swift_code": "BRASBRRJXXX",
        }

    def test_put_rejects_e5_not_homologated_fields(self, client):
        """E5 leftovers stay out — no proven controlled upstream change."""
        v, r = _auth()
        for field in (
            "simp_regime_code",
            "linked_customer_code",
            "linked_customer_store",
        ):
            with v, r:
                resp = client.put(
                    "/suppliers/000001/01",
                    json={"fornecedor": {field: "1"}},
                    headers={"Authorization": "Bearer t"},
                )
            assert resp.status_code == 422, field


class TestOperationStatus:
    _OP = "a43b7ba2-c1b3-486a-bf9e-6731200817d4"

    def _op_payload(self, status="CONFIRMED"):
        return {
            "success": True,
            "data": {
                "operation_id": self._OP,
                "status": status,
                "http_status": 200,
                "resource_key": "99988801",
                "correlation_id": "c-1",
                "created_at": "2026-10-21T09:00:00-03:00",
                "acknowledged_at": "2026-10-21T09:00:01-03:00",
                "confirmed_at": "2026-10-21T09:00:02-03:00" if status == "CONFIRMED" else None,
                "error_details": None,
                "confirmation_evidence": {"result": "match" if status == "CONFIRMED" else "unverifiable"},
                "request_payload": {"fields": {"tax_id": "[REDACTED]"}},
            },
        }

    def test_missing_bearer_401(self, client):
        assert client.get(f"/suppliers/operations/{self._OP}").status_code == 401

    def test_no_access_403(self, client):
        v, r = _auth(permissions={"supplies.manage"})
        with v, r:
            assert client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            ).status_code == 403

    def test_malformed_uuid_422(self, client):
        v, r = _auth()
        with v, r:
            assert client.get(
                "/suppliers/operations/not-a-uuid",
                headers={"Authorization": "Bearer t"},
            ).status_code == 422

    def test_operation_segment_does_not_hit_supplier_detail(self, client):
        """Static 'operations' segment must win over /<code>/<store>."""
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = self._op_payload("ACKNOWLEDGED")
            resp = client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        gw.get.assert_called_once_with(
            f"/integrations/operations/{self._OP}", access_token="user-jwt"
        )

    def test_confirmed_projects_outcome(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = self._op_payload("CONFIRMED")
            resp = client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            )
        body = resp.get_json()
        assert body["outcome"] == "confirmed"
        assert body["persistence_proven"] is True
        assert body["operation_id"] == self._OP
        assert "request_payload" not in body

    def test_unknown_maps_indeterminate(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = self._op_payload("UNKNOWN")
            resp = client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            )
        body = resp.get_json()
        assert body["outcome"] == "indeterminate"
        assert body["persistence_proven"] is False

    def test_error_details_code_becomes_tracking_warning(self, client):
        v, r = _auth()
        payload = self._op_payload("REJECTED")
        payload["data"]["error_details"] = {"code": "MATA020_INVALID"}
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.return_value = payload
            resp = client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            )
        body = resp.get_json()
        assert body["outcome"] == "rejected"
        assert body["tracking_warning"] == "MATA020_INVALID"

    def test_upstream_404_maps_not_found(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError("nf", status_code=404)
            assert client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            ).status_code == 404

    def test_upstream_403_propagates_denial_code(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                "denied", status_code=403, code="INTEGRATION_OPERATION_FORBIDDEN"
            )
            resp = client.get(
                f"/suppliers/operations/{self._OP}",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "INTEGRATION_OPERATION_FORBIDDEN"

    def test_post_response_surfaces_operation_id(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.post.return_value = {
                "success": True,
                "data": {"operation_id": self._OP, "creation_confirmed": False},
            }
            resp = client.post(
                "/suppliers",
                json={"fornecedor": {"supplier_name": "X"}},
                headers={"Authorization": "Bearer t"},
            )
        body = resp.get_json()
        assert body["operation_id"] == self._OP
        assert body["acknowledged"] is True

    def test_put_response_surfaces_operation_id(self, client):
        v, r = _auth()
        with v, r, patch(
            "app.interfaces.http.routes.suppliers_routes._GATEWAY"
        ) as gw:
            gw.put.return_value = {
                "success": True,
                "data": {
                    "operation_id": self._OP,
                    "update_acknowledged": True,
                    "persistence_proven": True,
                },
            }
            resp = client.put(
                "/suppliers/000001/01",
                json={"fornecedor": {"supplier_name": "N"}},
                headers={"Authorization": "Bearer t"},
            )
        body = resp.get_json()
        assert body["operation_id"] == self._OP
        assert body["persistence_proven"] is True


class TestSupplierCatalogs:
    _ENVELOPE = {
        'success': True,
        'data': {
            'catalog': 'states',
            'items': [{'code': 'SC', 'label': 'SANTA CATARINA', 'disabled': False}],
            'has_more': False,
            'total': 1,
        },
        'meta': {'operation_id': 'list_supplies_supplier_catalog_items'},
    }

    def test_missing_bearer_401(self, client):
        assert client.get('/suppliers/catalogs/states').status_code == 401

    def test_no_access_403(self, client):
        v, r = _auth(permissions={'supplies.manage'})
        with v, r:
            assert client.get(
                '/suppliers/catalogs/states',
                headers={'Authorization': 'Bearer t'},
            ).status_code == 403

    def test_known_catalog_proxies_s2s(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = self._ENVELOPE
            resp = client.get(
                '/suppliers/catalogs/payment-conditions?query=30&limit=10',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['items'][0]['code'] == 'SC'
        gw.get.assert_called_once_with(
            '/supplies/supplier-catalogs/payment-conditions',
            access_token='user-jwt',
            params={'query': '30', 'limit': '10'},
        )

    def test_unknown_catalog_422_no_upstream_call(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            resp = client.get(
                '/suppliers/catalogs/orders',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 422
        gw.get.assert_not_called()

    def test_municipalities_forward_state_filter(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = self._ENVELOPE
            resp = client.get(
                '/suppliers/catalogs/municipalities?state=SC&query=cha',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 200
        gw.get.assert_called_once_with(
            '/supplies/supplier-catalogs/municipalities',
            access_token='user-jwt',
            params={'state': 'SC', 'query': 'cha'},
        )

    def test_limit_is_bounded(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = self._ENVELOPE
            client.get(
                '/suppliers/catalogs/countries?limit=9999',
                headers={'Authorization': 'Bearer t'},
            )
        assert gw.get.call_args.kwargs['params']['limit'] == '500'

    def test_upstream_403_propagates_code(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                'denied', status_code=403, code='S2S_SCOPE_DENIED'
            )
            resp = client.get(
                '/suppliers/catalogs/states',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 403
        assert resp.get_json()['code'] == 'S2S_SCOPE_DENIED'

class TestPostalCodeLookup:
    """INT-CEP-01 — CEP via api-delpi (owner da integração), S2S.

    O BFF não conhece ViaCEP/BrasilAPI: só valida formato, delega via
    ``_GATEWAY`` e preserva o envelope público do Portal.
    """

    _UPSTREAM_FOUND = {
        'success': True,
        'data': {
            'postal_code': '01310100',
            'found': True,
            'street': 'Avenida Paulista',
            'district': 'Bela Vista',
            'city': 'São Paulo',
            'state': 'SP',
            'ibge_city_code': '3550308',
            'source': 'viacep',
            'result_type': 'street',
        },
    }

    def test_missing_bearer_401(self, client):
        assert client.get('/suppliers/postal-codes/01310100').status_code == 401

    def test_no_access_403(self, client):
        v, r = _auth(permissions={'supplies.manage'})
        with v, r:
            assert client.get(
                '/suppliers/postal-codes/01310100',
                headers={'Authorization': 'Bearer t'},
            ).status_code == 403

    def test_valid_masked_cep_proxies_and_returns(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = self._UPSTREAM_FOUND
            resp = client.get(
                '/suppliers/postal-codes/01310-100',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['found'] is True
        assert body['ibge_city_code'] == '3550308'
        assert body['street'] == 'Avenida Paulista'
        assert body['source'] == 'viacep'
        assert body['result_type'] == 'street'
        gw.get.assert_called_once_with(
            '/addresses/postal-codes/01310100', access_token='user-jwt'
        )

    def test_partial_municipality_result_passes_through(self, client):
        """89120000 — CEP geral: street/district vazios, IBGE presente."""
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = {
                'success': True,
                'data': {
                    'postal_code': '89120000',
                    'found': True,
                    'street': None,
                    'district': None,
                    'city': 'Timbó',
                    'state': 'SC',
                    'ibge_city_code': '4218202',
                    'source': 'brasilapi',
                    'result_type': 'municipality',
                },
            }
            resp = client.get(
                '/suppliers/postal-codes/89120000',
                headers={'Authorization': 'Bearer t'},
            )
        body = resp.get_json()
        assert resp.status_code == 200
        assert body['found'] is True
        assert body['street'] == '' and body['district'] == ''
        assert body['city'] == 'Timbó' and body['ibge_city_code'] == '4218202'
        assert body['result_type'] == 'municipality'

    def test_invalid_cep_rejected_before_upstream(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            resp = client.get(
                '/suppliers/postal-codes/123',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 422
        gw.get.assert_not_called()

    def test_cep_not_found_returns_found_false(self, client):
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.return_value = {
                'success': True,
                'data': {
                    'postal_code': '99999999',
                    'found': False,
                    'source': 'postal_address_providers',
                    'result_type': 'municipality',
                },
            }
            resp = client.get(
                '/suppliers/postal-codes/99999999',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 200
        assert resp.get_json()['found'] is False

    def test_upstream_timeout_maps_504(self, client):
        from app.infrastructure.gateways.delpi_api_gateway import (
            DelpiApiGatewayError,
        )
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError('api-delpi timeout')
            resp = client.get(
                '/suppliers/postal-codes/01310100',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 504
        assert resp.get_json()['code'] == 'provider_unreachable'

    def test_upstream_provider_error_maps_502(self, client):
        from app.infrastructure.gateways.delpi_api_gateway import (
            DelpiApiGatewayError,
        )
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                'api-delpi server error', status_code=502
            )
            resp = client.get(
                '/suppliers/postal-codes/01310100',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 502
        assert resp.get_json()['code'] == 'provider_error'

    def test_upstream_s2s_denial_propagates(self, client):
        from app.infrastructure.gateways.delpi_api_gateway import (
            DelpiApiGatewayError,
        )
        v, r = _auth()
        with v, r, patch(
            'app.interfaces.http.routes.suppliers_routes._GATEWAY'
        ) as gw:
            gw.get.side_effect = DelpiApiGatewayError(
                'denied', status_code=403, code='S2S_CLIENT_DENIED'
            )
            resp = client.get(
                '/suppliers/postal-codes/01310100',
                headers={'Authorization': 'Bearer t'},
            )
        assert resp.status_code == 403
        assert resp.get_json()['code'] == 'S2S_CLIENT_DENIED'


class TestPostalLookupBoundaries:
    """O BFF não pode conhecer providers externos nem consultá-los."""

    def test_bff_has_no_direct_provider_gateway(self):
        import app.interfaces.http.routes.suppliers_routes as routes
        assert not hasattr(routes, '_POSTAL_GATEWAY')
        source = open(routes.__file__, encoding='utf-8').read()
        assert 'viacep' not in source.lower()
        assert 'brasilapi' not in source.lower()
        assert 'postal_address_gateway' not in source

    def test_no_direct_provider_module_in_supplies_api(self):
        import pathlib
        gw_dir = (
            pathlib.Path(__file__).resolve().parent.parent
            / 'app' / 'infrastructure' / 'gateways'
        )
        assert not (gw_dir / 'postal_address_gateway.py').exists()
