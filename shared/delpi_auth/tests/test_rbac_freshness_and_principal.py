"""Direct contract tests for shared-auth material-write primitives.

``load_user_rbac(force_refresh=True)`` and the canonical
``principal_type`` marker were introduced for governed material writes.
These tests prove the implementation — not just its consumption — so the
transversal contract has first-party evidence.
"""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

import httpx
import pytest

import delpi_auth.middleware.fastapi_auth as fa


def run(coro):
    return asyncio.run(coro)


def _seed_cache(token: str, data: dict, *, fresh: bool) -> None:
    now = time.monotonic()
    fa._RBAC_CACHE[fa._cache_key(token)] = (
        now + 60 if fresh else now - 1,   # expires_at
        now + 900,                        # stale_until (valid in both cases)
        data,
    )


def _clear_cache():
    fa._RBAC_CACHE.clear()
    fa._RBAC_LOCKS.clear()


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    """Async context manager standing in for ``httpx.AsyncClient``."""

    calls: list[str] = []
    response: _FakeResponse | None = None
    error: Exception | None = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None):
        _FakeClient.calls.append(url)
        if _FakeClient.error is not None:
            raise _FakeClient.error
        return _FakeClient.response


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    _FakeClient.calls = []
    _FakeClient.response = None
    _FakeClient.error = None
    _clear_cache()
    monkeypatch.setattr(fa.httpx, "AsyncClient", _FakeClient)
    yield
    _clear_cache()


OLD = {"permissions": ["transformometro.access"], "is_superadmin": False}
NEW = {"permissions": [], "is_superadmin": False, "revoked": True}
TOKEN = "tok-material-write"


# ---------------------------------------------------------------------------
# force_refresh contract
# ---------------------------------------------------------------------------


def test_force_refresh_ignores_fresh_cache():
    _seed_cache(TOKEN, OLD, fresh=True)
    _FakeClient.response = _FakeResponse(200, NEW)

    result = run(fa.load_user_rbac(TOKEN, force_refresh=True))

    assert _FakeClient.calls, "Core /me deve ser consultada"
    assert result == NEW, "cache fresh anterior não pode ser retornado"
    assert result is not OLD


def test_force_refresh_never_uses_stale_fallback():
    # Stale-but-valid entry — under legacy semantics it would be served.
    _seed_cache(TOKEN, OLD, fresh=False)
    _FakeClient.error = httpx.RequestError("Core down")

    with pytest.raises(httpx.RequestError):
        run(fa.load_user_rbac(TOKEN, force_refresh=True))

    # Fail-closed proof: exception propagated, stale value never returned.
    assert _FakeClient.calls, "Core foi tentada"


def test_force_refresh_core_failure_not_cached(monkeypatch):
    _FakeClient.error = RuntimeError("lookup failed")
    with pytest.raises(RuntimeError):
        run(fa.load_user_rbac(TOKEN, force_refresh=True))


def test_default_reuses_fresh_cache():
    _seed_cache(TOKEN, OLD, fresh=True)
    _FakeClient.error = RuntimeError("must not be called")

    result = run(fa.load_user_rbac(TOKEN))

    assert result == OLD
    assert _FakeClient.calls == [], "cache fresh deve ser reutilizado"


def test_default_uses_stale_on_failure():
    _seed_cache(TOKEN, OLD, fresh=False)
    _FakeClient.error = httpx.RequestError("Core down")

    result = run(fa.load_user_rbac(TOKEN))

    assert result == OLD, "stale fallback é o contrato legado para reads"


def test_default_expired_stale_window_propagates():
    now = time.monotonic()
    fa._RBAC_CACHE[fa._cache_key(TOKEN)] = (now - 100, now - 10, OLD)
    _FakeClient.error = httpx.RequestError("Core down")

    with pytest.raises(httpx.RequestError):
        run(fa.load_user_rbac(TOKEN))


# ---------------------------------------------------------------------------
# principal_type — real middleware branches
# ---------------------------------------------------------------------------


def _request(path="/x", headers=None):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        headers=headers or {},
        state=SimpleNamespace(),
    )


async def _next_ok(request):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=200, content={"ok": True})


def test_service_token_mints_service_principal(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    req = _request(
        path="/transformometro/diagnostics",
        headers={"X-Delpi-Service-Token": "svc-secret"},
    )

    resp = run(fa.jwt_middleware(req, _next_ok))

    assert resp.status_code == 200
    user = req.state.user
    assert user.principal_type == "service"
    # Contrato anterior preservado — só o marcador foi adicionado.
    assert user.is_superadmin is True
    assert user.access_token is None


def test_jwt_user_mints_user_principal(monkeypatch):
    monkeypatch.setattr(
        fa,
        "validate_token",
        lambda t: {"sub": "u1", "email": "u@delpi", "sid": "s1"},
    )

    async def fake_rbac(token, *, force_refresh=False):
        return {
            "id": "u1", "email": "u@delpi",
            "permissions": ["transformometro.access"],
            "is_superadmin": False,
        }

    monkeypatch.setattr(fa, "load_user_rbac", fake_rbac)
    req = _request(
        path="/transformometro/diagnostics",
        headers={"Authorization": "Bearer user-jwt"},
    )

    resp = run(fa.jwt_middleware(req, _next_ok))

    assert resp.status_code == 200
    user = req.state.user
    assert user.principal_type == "user"
    assert user.is_superadmin is False


def test_jwt_fallback_rbac_unavailable_still_user_principal(monkeypatch):
    monkeypatch.setattr(
        fa,
        "validate_token",
        lambda t: {"sub": "u1", "email": "u@delpi", "sid": "s1"},
    )

    async def failing_rbac(token, *, force_refresh=False):
        raise RuntimeError("Core down")

    monkeypatch.setattr(fa, "load_user_rbac", failing_rbac)
    req = _request(
        path="/transformometro/diagnostics",
        headers={"Authorization": "Bearer user-jwt"},
    )

    resp = run(fa.jwt_middleware(req, _next_ok))

    assert resp.status_code == 200
    user = req.state.user
    assert user.principal_type == "user"
    assert user.rbac_unavailable is True
    assert user.permissions == []
    assert user.is_superadmin is False
