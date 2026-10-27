"""Contrato real de load_user_rbac (delpi_auth) — cache, stale, fail-closed.

Testa a resolução Core /me diretamente, com o client HTTP mockado:
o comportamento observado aqui é o que o middleware aplica em produção.
"""

import time

import httpx
import pytest

import delpi_auth.middleware.fastapi_auth as fastapi_auth_module


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        if self._payload is None:
            raise ValueError("invalid json")
        return self._payload


class _FakeAsyncClient:
    """AsyncClient fake — ``behavior`` controla a resposta do GET /me."""

    def __init__(self, behavior, *args, **kwargs):
        self._behavior = behavior

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None):
        self._behavior["calls"] += 1
        kind, value = self._behavior["action"]
        if kind == "raise":
            raise value
        return _FakeResponse(value[0], value[1])


def _client_factory(behavior):
    def _factory(*args, **kwargs):
        return _FakeAsyncClient(behavior, *args, **kwargs)

    return _factory


@pytest.fixture
def http_behavior(monkeypatch):
    behavior = {
        "calls": 0,
        "action": ("response", (200, {"permissions": ["engineering.access"]})),
    }
    monkeypatch.setattr(
        fastapi_auth_module.httpx, "AsyncClient", _client_factory(behavior)
    )
    return behavior


@pytest.mark.asyncio
async def test_rbac_lookup_success_caches(http_behavior):
    data = await fastapi_auth_module.load_user_rbac("token-a")
    assert data["permissions"] == ["engineering.access"]
    assert http_behavior["calls"] == 1

    cached = await fastapi_auth_module.load_user_rbac("token-a")
    assert cached is data
    assert http_behavior["calls"] == 1  # cache hit — sem nova chamada


@pytest.mark.asyncio
async def test_rbac_lookup_non_200_raises(http_behavior):
    http_behavior["action"] = ("response", (500, {}))
    with pytest.raises(RuntimeError):
        await fastapi_auth_module.load_user_rbac("token-b")


@pytest.mark.asyncio
async def test_rbac_lookup_timeout_without_cache_raises(http_behavior):
    http_behavior["action"] = ("raise", httpx.TimeoutException("timeout"))
    with pytest.raises(httpx.TimeoutException):
        await fastapi_auth_module.load_user_rbac("token-c")


@pytest.mark.asyncio
async def test_rbac_lookup_uses_stale_cache_on_failure(http_behavior, monkeypatch):
    """Política oficial: TTL normal 60s + stale 900s — Core-down serve stale."""
    key = fastapi_auth_module._cache_key("token-d")
    stale_data = {"permissions": ["engineering.access"], "stale": True}
    now = time.monotonic()
    fastapi_auth_module._RBAC_CACHE[key] = (
        now - 1,  # fresh TTL já expirou
        now + 600,  # ainda dentro da janela stale
        stale_data,
    )
    http_behavior["action"] = ("raise", httpx.TimeoutException("timeout"))
    data = await fastapi_auth_module.load_user_rbac("token-d")
    assert data is stale_data


@pytest.mark.asyncio
async def test_rbac_lookup_force_refresh_disables_stale(http_behavior):
    """force_refresh (escritas sensíveis) é fail-closed: stale não resgata."""
    key = fastapi_auth_module._cache_key("token-e")
    now = time.monotonic()
    fastapi_auth_module._RBAC_CACHE[key] = (
        now - 1,
        now + 600,
        {"permissions": ["engineering.access"]},
    )
    http_behavior["action"] = ("raise", httpx.TimeoutException("timeout"))
    with pytest.raises(httpx.TimeoutException):
        await fastapi_auth_module.load_user_rbac("token-e", force_refresh=True)


@pytest.mark.asyncio
async def test_rbac_lookup_expired_stale_raises(http_behavior):
    key = fastapi_auth_module._cache_key("token-f")
    now = time.monotonic()
    fastapi_auth_module._RBAC_CACHE[key] = (
        now - 900,
        now - 60,  # janela stale também expirada
        {"permissions": []},
    )
    http_behavior["action"] = ("raise", httpx.TimeoutException("timeout"))
    with pytest.raises(httpx.TimeoutException):
        await fastapi_auth_module.load_user_rbac("token-f")


@pytest.mark.asyncio
async def test_service_token_absent_without_env(monkeypatch):
    from delpi_auth.service_token import (
        headers_have_valid_internal_service_token,
    )

    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    assert not headers_have_valid_internal_service_token(
        {"X-Delpi-Service-Token": "anything"}
    )
