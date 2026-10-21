"""GET /closing/stock-inventory — BFF contract tests (R03/P7, doc 49).

Chain under test: middleware (JWT + RBAC snapshot) → principal_type/user
guard → ``controllership-finance.access`` → S2S gateway → typed errors.
The producer stays fail-closed on scope; the BFF relays, never overrides.
Branch is a data filter only — no per-branch permission exists.
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
PERIOD = "period=2026-09"
ROUTE = "/closing/stock-inventory"


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
    response = _client().get(f"{ROUTE}?{PERIOD}")
    assert response.status_code == 401
    gateway.get.assert_not_called()


def test_manage_only_is_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 403
    gateway.get.assert_not_called()


def test_no_permissions_is_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 403


def test_service_principal_denied(monkeypatch, gateway):
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 403
    gateway.get.assert_not_called()


def test_rbac_unavailable_fails_closed(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 503
    gateway.get.assert_not_called()


# --- filters (branch is data scope only) -------------------------------------


def test_routes_to_stock_inventory_path(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 200
    path = gateway.get.call_args.args[0]
    assert path == "/financeiro/stock-inventory"
    params = gateway.get.call_args.kwargs["params"]
    assert params["period"] == "2026-09"
    assert params["branch"] == "all"
    assert params["report_scope"] == "all_products"


def test_branch_02_is_plain_filter(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(_client(), f"{ROUTE}?{PERIOD}&branch=02")
    assert response.status_code == 200
    assert gateway.get.call_args.kwargs["params"]["branch"] == "02"


def test_invalid_branch_rejected(gateway):
    response = _get(_client(), f"{ROUTE}?{PERIOD}&branch=99")
    assert response.status_code == 422
    gateway.get.assert_not_called()


def test_invalid_period_rejected(gateway):
    assert _get(_client(), f"{ROUTE}?period=2026-13").status_code == 422
    gateway.get.assert_not_called()


def test_missing_period_rejected(gateway):
    assert _get(_client(), ROUTE).status_code == 422


def test_report_scope_and_warehouse_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    response = _get(
        _client(),
        f"{ROUTE}?{PERIOD}&report_scope=mp_pi_pa&warehouse=03&page=2",
    )
    assert response.status_code == 200
    params = gateway.get.call_args.kwargs["params"]
    assert params["report_scope"] == "mp_pi_pa"
    assert params["warehouse"] == "03"
    assert params["page"] == 2


def test_invalid_report_scope_rejected(gateway):
    assert (
        _get(_client(), f"{ROUTE}?{PERIOD}&report_scope=official_p7").status_code
        == 422
    )


def test_delegated_bearer_forwarded(gateway):
    gateway.get.return_value = {"success": True, "data": {"items": []}}
    _get(_client(), f"{ROUTE}?{PERIOD}")
    assert gateway.get.call_args.kwargs["access_token"] == TOKEN


# --- upstream error mapping --------------------------------------------------


def test_scope_unavailable_relays_typed_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["data"]["error"]["code"] == "scope_unavailable"


def test_upstream_401_maps_401(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error", status_code=401
    )
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 401


def test_upstream_403_maps_403(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi client error", status_code=403
    )
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 403


def test_upstream_timeout_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError("api-delpi timeout")
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 503


def test_upstream_500_maps_503(gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "api-delpi server error", status_code=500
    )
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 503


def test_upstream_unexpected_body_maps_502(gateway):
    gateway.get.return_value = ["not", "an", "envelope"]
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 502


# --- status propagation ------------------------------------------------------


def test_success_unwraps_data(gateway):
    payload = {
        "period": "2026-09",
        "referenceDate": "2026-09-30",
        "status": "available",
        "officialP7": False,
        "parityStatus": "TEST_NOT_RUN",
        "items": [{"productCode": "P1"}],
        "historicalTotal": "10576487.8400",
    }
    gateway.get.return_value = {
        "success": True,
        "message": "Stock inventory snapshot loaded successfully.",
        "data": payload,
    }
    response = _get(_client(), f"{ROUTE}?{PERIOD}&branch=02")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == payload
    assert body["meta"]["operationId"] == "get_closing_stock_inventory"


def test_source_missing_status_propagates(gateway):
    payload = {
        "status": "source_missing",
        "branchesAvailable": [],
        "branchesMissing": ["01"],
        "historicalTotal": None,
        "items": [],
    }
    gateway.get.return_value = {"success": True, "data": payload}
    response = _get(_client(), f"{ROUTE}?{PERIOD}&branch=01")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "source_missing"
    assert response.json()["data"]["historicalTotal"] is None


def test_incomplete_status_propagates(gateway):
    payload = {
        "status": "incomplete",
        "branchesAvailable": ["02"],
        "branchesMissing": ["01"],
        "historicalTotal": "10576487.8400",
        "items": [],
    }
    gateway.get.return_value = {"success": True, "data": payload}
    response = _get(_client(), f"{ROUTE}?{PERIOD}&branch=all")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "incomplete"
