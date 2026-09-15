"""Auth-facing tests for MCP surface (no live Keycloak)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.middleware.auth_middleware import (
    _is_mcp_data_path,
    _is_public_delpi_path,
    jwt_middleware,
)


def _request(path: str, headers: dict | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_mcp_without_bearer_returns_401_with_challenge() -> None:
    call_next = AsyncMock()
    response = await jwt_middleware(_request("/mcp"), call_next)
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "resource_metadata=" in response.headers["WWW-Authenticate"]
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_mcp_service_token_rejected() -> None:
    call_next = AsyncMock()
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=True,
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer user-token"}),
            call_next,
        )
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_mcp_invalid_token_keeps_challenge_header() -> None:
    call_next = AsyncMock()
    unauthorized = JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    async def _base(request, next_call):
        return unauthorized

    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_base,
    ):
        response = await jwt_middleware(
            _request("/apps/api-delpi/mcp", {"Authorization": "Bearer bad"}),
            call_next,
        )
    assert response.status_code == 401
    assert "resource_metadata=" in response.headers.get("WWW-Authenticate", "")


def test_path_helpers() -> None:
    assert _is_mcp_data_path("/mcp") is True
    assert _is_mcp_data_path("/mcp/") is True
    assert _is_public_delpi_path("/.well-known/oauth-protected-resource/mcp") is True
