"""GET /closing/stock-inventory/export — BFF binary passthrough tests.

The CSV (metadata header, SHA-256 hash, parity watermark) is produced by
api-delpi — the data owner. The BFF adds the ``access`` gate and relays
the file and typed errors verbatim; ``access.dre`` never reaches it.
"""

from __future__ import annotations

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
DRE = "controllership-finance.access.dre"
TOKEN = "viewer-test-token"
PERIOD = "period=2026-09"
ROUTE = "/closing/stock-inventory/export"

CSV_BYTES = b"\xef\xbb\xbf# competencia=2026-09\nproduct_code\nP1\n"
DISPOSITION = 'attachment; filename="p7-inventory-2026-09-all-all_products.csv"'


def _claims(**overrides) -> dict:
    claims = {
        "sub": "user-1",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
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
    fake.get_bytes.return_value = (CSV_BYTES, DISPOSITION)
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


# --- authorization (same fail-closed chain as the query) ---------------------


def test_export_requires_bearer(gateway):
    assert _client().get(f"{ROUTE}?{PERIOD}").status_code == 401
    gateway.get_bytes.assert_not_called()


def test_export_manage_only_forbidden(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 403
    gateway.get_bytes.assert_not_called()


def test_export_dre_only_forbidden(_auth_pipeline, gateway):
    """AC10 — ``access.dre`` alone never authorizes the internal report."""
    _auth_pipeline["rbac"] = _rbac(permissions=[DRE])
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 403
    gateway.get_bytes.assert_not_called()


def test_export_rbac_unavailable_fails_closed(_auth_pipeline, gateway):
    _auth_pipeline["rbac"] = _rbac(rbac_unavailable=True)
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 503
    gateway.get_bytes.assert_not_called()


# --- contract ----------------------------------------------------------------


def test_export_streams_upstream_bytes_and_disposition(gateway):
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == DISPOSITION
    assert response.content == CSV_BYTES


def test_export_targets_upstream_export_route(gateway):
    _get(_client(), f"{ROUTE}?{PERIOD}&branch=01&warehouse=03")
    call = gateway.get_bytes.call_args
    assert call.args[0] == "/financeiro/stock-inventory/export"
    params = call.kwargs["params"]
    assert params["period"] == "2026-09"
    assert params["branch"] == "01"
    assert params["warehouse"] == "03"
    assert params["format"] == "csv"


def test_export_scope_forwarded(gateway):
    _get(_client(), f"{ROUTE}?{PERIOD}&report_scope=mp_pi_pa")
    assert (
        gateway.get_bytes.call_args.kwargs["params"]["report_scope"]
        == "mp_pi_pa"
    )


def test_export_rejects_unknown_format(gateway):
    assert (
        _get(_client(), f"{ROUTE}?{PERIOD}&format=xlsx").status_code == 422
    )
    gateway.get_bytes.assert_not_called()


def test_export_invalid_branch_rejected(gateway):
    assert _get(_client(), f"{ROUTE}?{PERIOD}&branch=99").status_code == 422
    gateway.get_bytes.assert_not_called()


# --- upstream error mapping ----------------------------------------------------


def test_export_scope_unavailable_relays_403(gateway):
    gateway.get_bytes.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=403,
        error_code="scope_unavailable",
    )
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 403
    assert response.json()["data"]["error"]["code"] == "scope_unavailable"


def test_export_not_exportable_relays_409(gateway):
    """``source_missing`` upstream — never an empty CSV masquerading."""
    gateway.get_bytes.side_effect = DelpiApiGatewayError(
        "api-delpi client error",
        status_code=409,
        error_code="not_exportable",
    )
    response = _get(_client(), f"{ROUTE}?{PERIOD}")
    assert response.status_code == 409
    assert response.json()["data"]["error"]["code"] == "not_exportable"


def test_export_upstream_timeout_maps_503(gateway):
    gateway.get_bytes.side_effect = DelpiApiGatewayError(
        "api-delpi timeout"
    )
    assert _get(_client(), f"{ROUTE}?{PERIOD}").status_code == 503
