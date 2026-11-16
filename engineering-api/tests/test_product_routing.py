"""GET /v1/products/{code}/routing — roteiro de fabricação (SG2).

Delegação governada ao owner (`GET /products/{code}/guide` na
api-delpi): Bearer humano propagado, estados honestos
available/forbidden/not_found/unavailable, AuthZ `engineering.access`
na borda — sem reprocessamento nem operações fabricadas.
"""

from __future__ import annotations

import engineering_app.interface.http.routes.product_routes as product_routes


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class _AuxStub:
    """Stub do source delegado — contrato pós-adapter."""

    def __init__(self, result):
        self._result = result
        self.calls = {}

    async def fetch_product_guide(self, ctx, **kw):
        self.calls["guide"] = kw
        self.calls["access_token"] = ctx.access_token
        return self._result


def _install_stub(monkeypatch, result):
    stub = _AuxStub(result)
    monkeypatch.setattr(
        product_routes, "build_delegated_auxiliary_source", lambda: stub
    )
    return stub


def _available():
    return {
        "status": "available",
        "data": {
            "items": [
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90264302",
                    "operation_code": "010",
                    "operation_description": "CORTE",
                    "resource_code": "LASER01",
                    "work_center": "CT10",
                    "setup_hours": 0.5,
                    "standard_time_hour_mil": 120.0,
                    "operation_type": "1",
                    "bom_level": 0,
                }
            ],
            "total": 1,
        },
    }


def test_routing_returns_owner_payload(client, jwks_env, core_rbac, monkeypatch):
    stub = _install_stub(monkeypatch, _available())
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/90264302/routing?branch=01&max_depth=3",
        headers=_bearer(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert items[0]["operation_code"] == "010"
    assert items[0]["work_center"] == "CT10"
    assert stub.calls["guide"]["code"] == "90264302"
    assert stub.calls["guide"]["branch"] == "01"
    assert stub.calls["guide"]["max_depth"] == 3
    assert stub.calls["access_token"]


def test_routing_requires_auth(client):
    assert client.get("/v1/products/90264302/routing").status_code == 401


def test_routing_denied_without_engineering_access(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available())
    core_rbac["behavior"] = ("data", _rbac_payload([]))
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/90264302/routing", headers=_bearer(token)
    )
    assert resp.status_code == 403


def test_routing_forbidden_source_maps_403(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(
        monkeypatch, {"status": "forbidden", "reason": "owner_denied"}
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/90264302/routing", headers=_bearer(token)
    )
    assert resp.status_code == 403


def test_routing_not_found_maps_404(client, jwks_env, core_rbac, monkeypatch):
    _install_stub(
        monkeypatch, {"status": "not_found", "reason": "not_found"}
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/99999999/routing", headers=_bearer(token)
    )
    assert resp.status_code == 404


def test_routing_unavailable_maps_502(client, jwks_env, core_rbac, monkeypatch):
    _install_stub(
        monkeypatch, {"status": "unavailable", "reason": "timeout"}
    )
    token = jwks_env["make_token"]()
    resp = client.get(
        "/v1/products/90264302/routing", headers=_bearer(token)
    )
    assert resp.status_code == 502


def test_routing_openapi_declares_route(client):
    spec = client.get("/openapi.json").json()
    op = spec["paths"]["/v1/products/{product_code}/routing"]["get"]
    assert op["operationId"] == "get_product_routing"


def _rbac_payload(permissions, **overrides) -> dict:
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "roles": [],
        "groups": [],
        "permissions": list(permissions),
        "is_superadmin": False,
    }
    data.update(overrides)
    return data


def test_line_balance_reuses_domain(client, jwks_env, core_rbac, monkeypatch):
    """POST /v1/products/{code}/line-balance — mesmo domínio EVA."""
    stub = _install_stub(monkeypatch, _available())
    token = jwks_env["make_token"]()
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={"demand": 500, "available_minutes": 420},
        headers=_bearer(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["analysis_type"] == "routing.line_balance"
    assert data["data_class"] == "CALCULATED"
    assert data["parameters"]["demand"]["data_class"] == "PROVIDED"
    assert data["parameters"]["demand"]["value"] == 500
    assert stub.calls["access_token"] == token


def test_line_balance_requires_auth(client):
    resp = client.post("/v1/products/90264302/line-balance", json={})
    assert resp.status_code == 401


def test_line_balance_denied_without_engineering_access(
    client, jwks_env, core_rbac, monkeypatch
):
    core_rbac["behavior"] = ("data", _rbac_payload([]))
    token = jwks_env["make_token"]()
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={"demand": 500, "available_minutes": 420},
        headers=_bearer(token),
    )
    assert resp.status_code == 403


def test_line_balance_rejects_unknown_fields(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available())
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={"demand": 500, "equipment_constraint": "no-laser"},
        headers=_bearer(jwks_env["make_token"]()),
    )
    assert resp.status_code == 400
    assert "equipment_constraint" in resp.text


def test_line_balance_rejects_bad_bom_levels(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, _available())
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={"bom_levels": "all"},
        headers=_bearer(jwks_env["make_token"]()),
    )
    assert resp.status_code == 400


def test_line_balance_forbidden_maps_403(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, {"status": "forbidden", "data": None})
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={},
        headers=_bearer(jwks_env["make_token"]()),
    )
    assert resp.status_code == 403


def test_line_balance_not_found_maps_404(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, {"status": "not_found", "data": None})
    resp = client.post(
        "/v1/products/99999999/line-balance",
        json={},
        headers=_bearer(jwks_env["make_token"]()),
    )
    assert resp.status_code == 404


def test_line_balance_unavailable_maps_502(
    client, jwks_env, core_rbac, monkeypatch
):
    _install_stub(monkeypatch, {"status": "unavailable", "data": None})
    resp = client.post(
        "/v1/products/90264302/line-balance",
        json={},
        headers=_bearer(jwks_env["make_token"]()),
    )
    assert resp.status_code == 502


def test_line_balance_openapi_declares_route(client):
    spec = client.get("/openapi.json").json()
    op = spec["paths"]["/v1/products/{product_code}/line-balance"]["post"]
    assert op["operationId"] == "post_product_line_balance"
