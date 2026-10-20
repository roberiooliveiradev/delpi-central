"""GET /viewer-context — contrato IMP-MFE-HOME (D1=A / D2=A).

Cobre a cadeia real: middleware compartilhado (JWT + Core /me + stale D1)
→ guard de principal humano → capabilities. Nenhuma autorização é
derivada do JWT; ``principal_type != "user"`` é negado antes do bypass
de superadmin.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fa
from controllership_finance_app.main import app

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"

TOKEN = "viewer-test-token"


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
    """Determinístico: token válido + Core responde o rbac pedido."""

    rbac_holder = {"rbac": _rbac()}

    monkeypatch.setattr(fa, "request_has_valid_internal_service_token", lambda request: False)
    monkeypatch.setattr(fa, "validate_token", lambda token: _claims())
    monkeypatch.setattr(
        fa,
        "load_user_rbac",
        lambda token, *, force_refresh=False: _load_rbac_result(rbac_holder["rbac"]),
    )
    yield rbac_holder


def _client() -> TestClient:
    return TestClient(app)


def _get(client: TestClient, token: str = TOKEN):
    return client.get(
        "/viewer-context",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_viewer_context_requires_bearer_token():
    response = _client().get("/viewer-context")
    assert response.status_code == 401


def test_viewer_context_invalid_token_returns_401(monkeypatch):
    def _boom(_token):
        raise Exception("invalid signature")

    monkeypatch.setattr(fa, "validate_token", _boom)
    response = _get(_client())
    assert response.status_code == 401


def test_viewer_context_missing_claims_returns_401(monkeypatch):
    monkeypatch.setattr(fa, "validate_token", lambda _t: {"sub": "x", "email": None})
    assert _get(_client()).status_code == 401


def test_viewer_context_human_with_access_returns_200(_auth_pipeline):
    response = _get(_client())
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_viewer_context"
    assert body["data"] == {
        "firstName": "Ana",
        "displayName": "Ana Souza",
        "capabilities": {"access": True, "manage": False},
    }


def test_viewer_context_access_plus_manage(_auth_pipeline):
    _auth_pipeline["rbac"] = _rbac(permissions=[ACCESS, MANAGE])
    response = _get(_client())
    assert response.status_code == 200
    assert response.json()["data"]["capabilities"] == {
        "access": True,
        "manage": True,
    }


def test_viewer_context_manage_only_is_forbidden(_auth_pipeline):
    """``manage`` não implica ``access``."""
    _auth_pipeline["rbac"] = _rbac(permissions=[MANAGE])
    assert _get(_client()).status_code == 403


def test_viewer_context_no_permissions_is_forbidden(_auth_pipeline):
    _auth_pipeline["rbac"] = _rbac(permissions=[])
    assert _get(_client()).status_code == 403


def test_viewer_context_service_principal_is_denied(monkeypatch):
    """Service token minta ``principal_type="service"`` + superadmin —
    negado antes do bypass de superadmin."""
    monkeypatch.setattr(
        fa, "request_has_valid_internal_service_token", lambda request: True
    )
    response = _client().get(
        "/viewer-context",
        headers={"X-Delpi-Service-Token": "internal"},
    )
    assert response.status_code == 403


def test_viewer_context_core_unavailable_without_snapshot_is_503(monkeypatch):
    async def _down(_token, *, force_refresh=False):
        raise RuntimeError("core unreachable")

    monkeypatch.setattr(fa, "load_user_rbac", _down)
    response = _get(_client())
    assert response.status_code == 503


_REAL_LOAD_RBAC = fa.load_user_rbac


def test_viewer_context_valid_stale_snapshot_is_accepted(monkeypatch):
    """D1: snapshot previamente validado dentro da janela stale (≤900s)."""
    token = "viewer-stale-token"
    now = time.monotonic()
    fa._RBAC_CACHE[fa._cache_key(token)] = (
        now - 1,      # fresh expirado
        now + 900,    # stale válido
        _rbac(),
    )

    # Reinstala o load_user_rbac real (a fixture o substitui) com Core down.
    monkeypatch.setattr(fa, "load_user_rbac", _REAL_LOAD_RBAC)

    class _FailClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, headers=None):
            raise RuntimeError("core unreachable")

    monkeypatch.setattr(fa.httpx, "AsyncClient", _FailClient)
    try:
        response = _get(_client(), token=token)
    finally:
        fa._RBAC_CACHE.pop(fa._cache_key(token), None)
    assert response.status_code == 200


def test_viewer_context_expired_stale_snapshot_fails_closed(monkeypatch):
    """Stale fora da janela aprovada não autoriza: fail closed → 503."""
    token = "viewer-expired-stale-token"
    now = time.monotonic()
    fa._RBAC_CACHE[fa._cache_key(token)] = (
        now - 1000,
        now - 10,     # stale expirado
        _rbac(),
    )

    monkeypatch.setattr(fa, "load_user_rbac", _REAL_LOAD_RBAC)

    class _FailClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, headers=None):
            raise RuntimeError("core unreachable")

    monkeypatch.setattr(fa.httpx, "AsyncClient", _FailClient)
    try:
        response = _get(_client(), token=token)
    finally:
        fa._RBAC_CACHE.pop(fa._cache_key(token), None)
    assert response.status_code == 503


def test_viewer_context_first_name_falls_back_safely(monkeypatch, _auth_pipeline):
    """Sem given_name/name não inventa usuário: firstName é null e a UI
    cai na saudação genérica."""
    monkeypatch.setattr(
        fa,
        "validate_token",
        lambda _t: {"sub": "user-2", "email": "bruno@delpi.com.br"},
    )
    _auth_pipeline["rbac"] = _rbac(id="user-2", email="bruno@delpi.com.br", name=None)
    response = _get(_client())
    assert response.status_code == 200
    assert response.json()["data"]["firstName"] is None


def test_viewer_context_uses_display_name_when_no_given_name(monkeypatch, _auth_pipeline):
    monkeypatch.setattr(
        fa,
        "validate_token",
        lambda _t: {
            "sub": "user-3",
            "email": "carla@delpi.com.br",
            "name": "Carla Lima",
        },
    )
    _auth_pipeline["rbac"] = _rbac(id="user-3", email="carla@delpi.com.br", name="Carla Lima")
    response = _get(_client())
    assert response.status_code == 200
    assert response.json()["data"]["firstName"] == "Carla"


def test_viewer_context_human_superadmin_gets_manage_capability(_auth_pipeline):
    """Superadmin humano (principal_type=user) preserva o bypass canônico."""
    _auth_pipeline["rbac"] = _rbac(permissions=[], is_superadmin=True)
    response = _get(_client())
    assert response.status_code == 200
    assert response.json()["data"]["capabilities"] == {
        "access": True,
        "manage": True,
    }


def test_viewer_context_route_is_not_public():
    """Regressão: a rota não pode constar da lista de paths públicos."""
    from controllership_finance_app.middleware.auth_middleware import (
        _is_controllership_finance_public_path,
    )

    assert _is_controllership_finance_public_path("/viewer-context") is False
    assert (
        _is_controllership_finance_public_path(
            "/apps/controllership-finance-api/viewer-context"
        )
        is False
    )


def test_viewer_photo_requires_auth():
    assert _client().get("/viewer-photo").status_code == 401


def test_viewer_photo_service_principal_blocked(monkeypatch):
    monkeypatch.setattr(fa, "request_has_valid_internal_service_token", lambda request: True)
    assert _client().get("/viewer-photo", headers={"X-Delpi-Service-Token": "internal"}).status_code == 403


def _get_photo(client):
    return client.get("/viewer-photo", headers={"Authorization": "Bearer " + TOKEN})


def test_viewer_photo_proxies_only_image(monkeypatch):
    import httpx
    from controllership_finance_app.interface.http.routes import viewer_context_routes as routes

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, headers):
            assert url.endswith("/me/person-profile/photo")
            assert headers["Authorization"] == "Bearer " + TOKEN
            return httpx.Response(200, content=b"mock-image", headers={"content-type": "image/png"})

    monkeypatch.setattr(routes.httpx, "AsyncClient", FakeAsyncClient)
    response = _get_photo(_client())
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"mock-image"
    assert response.headers["cache-control"] == "private, no-store"


def test_viewer_photo_core_no_photo(monkeypatch):
    import httpx
    from controllership_finance_app.interface.http.routes import viewer_context_routes as routes

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, headers):
            return httpx.Response(404)

    monkeypatch.setattr(routes.httpx, "AsyncClient", FakeAsyncClient)
    assert _get_photo(_client()).status_code == 404
