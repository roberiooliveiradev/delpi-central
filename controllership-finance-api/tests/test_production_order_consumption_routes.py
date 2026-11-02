"""R04 production-order-consumption — BFF contract (Gate 061).

Pins the governed route: human principal + ``controllership-finance.access``
authorization, api-delpi S2S passthrough to the ``consumption-audit``
producer, operational officiality + pending parity, param mapping
(period → period_start/end) and typed error passthrough. The BFF never
recomputes consumption and never declares MATR860 equivalence.
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
R04 = "/closing/competences/2026-09/production-order-consumption"
R04_DETAIL = "/closing/competences/2026-09/production-order-consumption/OP001"


def _claims(**overrides) -> dict:
    claims = {
        "sub": "33333333-3333-4333-8333-333333333333",
        "email": "ana@delpi.com.br",
        "name": "Ana Souza",
    }
    claims.update(overrides)
    return claims


def _rbac(**overrides) -> dict:
    rbac = {
        "id": "33333333-3333-4333-8333-333333333333",
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
    monkeypatch.setattr(
        fa,
        "request_has_valid_internal_service_token",
        lambda request: False,
    )
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(_rbac()),
    )
    yield


@pytest.fixture
def gateway(monkeypatch):
    fake = MagicMock()
    fake.get.return_value = {
        "success": True,
        "data": {
            "orders": [
                {"productionOrder": "OP001"},
                {"productionOrder": "OP002"},
            ],
            "total": 2,
            "page": 1,
        },
        "message": "ok",
    }
    monkeypatch.setattr(
        "controllership_finance_app.interface.http.routes.production_order_consumption_routes.ApiDelpiSettlementsGateway",
        lambda: fake,
    )
    return fake


@pytest.fixture
def client():
    return TestClient(app)


def test_requires_authentication(client):
    resp = client.get(R04, params={"branch": "01"})
    assert resp.status_code in (401, 403)


def test_requires_branch(client, gateway):
    resp = client.get(R04, headers={"Authorization": "Bearer t"})
    assert resp.status_code == 422


def test_branch_must_be_01_or_02(client, gateway):
    resp = client.get(
        R04, params={"branch": "99"}, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code == 422


def test_happy_path_maps_period_and_projects(client, gateway):
    resp = client.get(
        R04,
        params={"branch": "01", "date_type": "emission", "page": 2},
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["officiality"] == "operational_view"
    assert data["officialParity"] == "pending"
    assert data["provenance"].startswith("api-delpi")
    assert len(data["limitations"]) >= 1
    assert data["orders"][0]["productionOrder"] == "OP001"
    call = gateway.get.call_args
    assert call.args[0] == "/supplies/consumption-audit/orders"
    params = call.kwargs["params"]
    assert params["period_start"] == "2026-09-01"
    assert params["period_end"] == "2026-09-30"
    assert params["branch"] == "01"
    assert params["page"] == 2
    assert params["date_type"] == "emission"


def test_optional_filters_forwarded(client, gateway):
    client.get(
        R04,
        params={
            "branch": "02",
            "search": "7026",
            "product": "ACO",
            "status": "A",
            "work_center": "CT-53",
            "operation": "050",
        },
        headers={"Authorization": "Bearer t"},
    )
    params = gateway.get.call_args.kwargs["params"]
    for key in ("search", "product", "status", "work_center", "operation"):
        assert key in params


def test_upstream_failure_mapped(client, gateway):
    gateway.get.side_effect = DelpiApiGatewayError(
        "Origem de dados financeiros indisponível.", status_code=503
    )
    resp = client.get(
        R04, params={"branch": "01"}, headers={"Authorization": "Bearer t"}
    )
    assert resp.status_code in (500, 502, 503)


def test_detail_route_calls_producer(client, gateway):
    gateway.get.return_value = {
        "success": True,
        "data": {"op": "OP001"},
        "message": "ok",
    }
    resp = client.get(
        R04_DETAIL,
        params={"branch": "01"},
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 200, resp.text
    call = gateway.get.call_args
    assert call.args[0] == "/supplies/consumption-audit/orders/OP001"
    assert call.kwargs["params"]["branch"] == "01"
    assert resp.json()["data"]["officialParity"] == "pending"
