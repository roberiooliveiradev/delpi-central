"""GET /closing/financial-settlements(+ /summary) — BFF contract tests.

Chain under test: middleware (JWT + RBAC snapshot) → principal_type/user
guard → ``controllership-finance.access`` → S2S gateway → typed errors.
The producer stays fail-closed on scope; the BFF relays, never overrides.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    DelpiApiGatewayError,
)
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
TOKEN = "viewer-test-token"
PERIOD = "start_date=2026-01-01&end_date=2026-01-31"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "given_name": "Ana",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
        "roles": [],
        "groups": [],
        "permissions": [ACCESS],
        "is_superadmin": False,
    }
    rbac.update(overrides)
    return rbac


async def _load_rbac_result(rbac: dict):
    return rbac


@pytest.fixture(autouse=True)
def _auth_pipeline(monkeypatch):
    rbac_holder = {"rbac": _rbac()}

    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: False
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(
            rbac_holder["rbac"]
        ),
    )
    yield rbac_holder


@pytest.fixture
def gateway(monkeypatch):
    fake = MagicMock()
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes.closing_routes."
        "ApiDelpiSettlementsGateway",
        lambda *a, **k: fake,
    )
    return fake


def _client() -> TestClient:
    return TestClient(app)


def _get(client, path, token: str = TOKEN):
    return client.get(path, headers={"Authorization": f"Bearer {token}"})


# --- authorization ----------------------------------------------------------


def test_requires_bearer_token(gateway):
    response = _client().get(
        f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 401
    gateway.get.assert_not_called()


def test_manage_only_is_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 403
    gateway.get.assert_not_called()


def test_no_permissions_is_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 403
    )


def test_service_principal_denied(monkeypatch, gateway):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 403
    gateway.get.assert_not_called()


def test_rbac_unavailable_fails_closed(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 503
    gateway.get.assert_not_called()


# --- side routing + params --------------------------------------------------


def test_payable_side_routes_to_payables(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 200
    path = gateway.get.call_args.args[0]
    assert path == "/financeiro/settlements/payables"


def test_receivable_side_routes_to_receivables(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(),
        f"/closing/financial-settlements?side=receivable&{PERIOD}"
        "&movement_type=BA&nature_code=100",
    )
    assert response.status_code == 200
    path = gateway.get.call_args.args[0]
    params = gateway.get.call_args.kwargs["params"]
    assert path == "/financeiro/settlements/receivables"
    assert params["movement_type"] == "BA"
    assert params["nature_code"] == "100"


def test_invalid_side_rejected(gateway):
    response = _get(
        _client(), f"/closing/financial-settlements?side=north&{PERIOD}"
    )
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_missing_side_rejected(gateway):
    response = _get(_client(), f"/closing/financial-settlements?{PERIOD}")
    assert response.status_code == 422


def test_summary_route_no_side(gateway):
    gateway.get.return_value = {"success": True, "data": {"groups": []}}
    response = _get(
        _client(), f"/closing/financial-settlements/summary?{PERIOD}"
    )
    assert response.status_code == 200
    assert gateway.get.call_args.args[0] == "/financeiro/settlements/summary"


def test_delegated_bearer_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
    assert gateway.get.call_args.kwargs["access_token"] == TOKEN


# --- upstream error mapping -------------------------------------------------


def test_scope_unavailable_relays_typed_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["data"]["error"]["code"] == "scope_unavailable"


def test_upstream_401_maps_401(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error", status_code=401
    )
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 401
    )


def test_upstream_403_maps_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error", status_code=403
    )
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 403
    )


def test_upstream_timeout_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 503
    )


def test_upstream_500_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error", status_code=500
    )
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 503
    )


def test_upstream_unexpected_body_maps_502(gateway):
    gateway.get.return_value = ["not", "an", "envelope"]
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 502
    )


def test_upstream_envelope_failure_maps_502(gateway):
    gateway.get.return_value = {"success": False, "message": "boom"}
    assert (
        _get(_client(), f"/closing/financial-settlements?side=payable&{PERIOD}")
        .status_code
        == 502
    )


def test_success_unwraps_data(gateway):
    payload = {
        "items": [{"settlementId": "ID1", "branchCode": None}],
        "officialTotals": False,
    }
    gateway.get.return_value = {
        "success": True,
        "message": "Payable settlement events loaded successfully.",
        "data": payload,
    }
    response = _get(
        _client(), f"/closing/financial-settlements?side=payable&{PERIOD}"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == payload
    assert body["meta"]["operationId"] == "get_closing_financial_settlements"
