"""OAuth/MCP contract tests (code-level; not live Keycloak go-live)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.application.external_capabilities.constants import MCP_TOOL_SEARCH_PRODUCTS
from app.interface.mcp.oauth_contract import (
    CANONICAL_MCP_RESOURCE_URL,
    MCP_AUTH_MODEL,
    MCP_OAUTH_SCOPES,
    MCP_RESOURCE_BINDING_SCOPE,
    SEARCH_PRODUCTS_SECURITY_SCHEMES,
    build_www_authenticate_challenge,
    missing_required_oauth_scopes,
    mcp_www_authenticate_meta,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
)
from app.interface.mcp.resource_metadata import build_oauth_protected_resource_metadata
from app.interface.mcp.server import create_mcp_server
from app.middleware.auth_middleware import jwt_middleware


def _request(path: str, headers: dict | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    return Request(scope)


def test_auth_model_is_transport_level() -> None:
    assert MCP_AUTH_MODEL == "TRANSPORT_REQUIRES_OAUTH"


def test_security_schemes_are_oauth2_without_rbac_codes() -> None:
    assert MCP_RESOURCE_BINDING_SCOPE == "mcp:tools"
    assert "mcp:tools" in MCP_OAUTH_SCOPES
    assert SEARCH_PRODUCTS_SECURITY_SCHEMES == [
        {"type": "oauth2", "scopes": list(MCP_OAUTH_SCOPES)}
    ]
    blob = json.dumps(SEARCH_PRODUCTS_SECURITY_SCHEMES)
    assert "ENGINEERING_LMP_ACCESS" not in blob
    assert "api-delpi.access" not in blob
    assert "dashboard-" not in blob


def test_list_tools_exposes_top_level_security_schemes() -> None:
    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 1
    tool = tools[0]
    dumped = tool.model_dump(by_alias=True)
    assert tool.name == MCP_TOOL_SEARCH_PRODUCTS
    assert dumped.get("securitySchemes") == SEARCH_PRODUCTS_SECURITY_SCHEMES
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.openWorldHint is False
    assert "ENGINEERING_LMP_ACCESS" not in json.dumps(dumped)


def test_resource_metadata_scopes_and_resource(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi")
    monkeypatch.delenv("MCP_RESOURCE_URL", raising=False)
    doc = build_oauth_protected_resource_metadata()
    assert doc["resource"] == CANONICAL_MCP_RESOURCE_URL
    assert doc["authorization_servers"] == [
        "https://minhadelpi.com.br/auth/realms/delpi"
    ]
    assert doc["scopes_supported"] == list(MCP_OAUTH_SCOPES)
    assert "mcp:tools" in doc["scopes_supported"]
    assert resolve_required_mcp_resource_audience() == CANONICAL_MCP_RESOURCE_URL


def test_www_authenticate_includes_error_fields(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    challenge = build_www_authenticate_challenge(
        error="invalid_token",
        error_description="Authentication required",
    )
    assert 'resource_metadata="https://minhadelpi.com.br/apps/api-delpi/.well-known/oauth-protected-resource"' in challenge
    assert 'error="invalid_token"' in challenge
    assert 'error_description="Authentication required"' in challenge
    assert "openid" in challenge


def test_tool_meta_www_authenticate_contract() -> None:
    meta = mcp_www_authenticate_meta(
        error="insufficient_scope",
        error_description="Required OAuth scopes are missing",
    )
    assert "mcp/www_authenticate" in meta
    assert isinstance(meta["mcp/www_authenticate"], list)
    assert 'error="insufficient_scope"' in meta["mcp/www_authenticate"][0]


@patch(
    "app.application.external_capabilities.product_search_service.require_product_search_access",
    side_effect=PermissionError("Unauthorized"),
)
def test_tool_returns_mcp_www_authenticate_on_unauthorized(_authz) -> None:
    mcp = create_mcp_server()
    tool = mcp._tool_manager.get_tool(MCP_TOOL_SEARCH_PRODUCTS)
    result = tool.fn(page=1, page_size=10)
    dumped = result.model_dump(by_alias=True)
    assert dumped["isError"] is True
    assert "mcp/www_authenticate" in dumped["_meta"]
    assert "Authentication required" in dumped["content"][0]["text"]


@patch(
    "app.application.external_capabilities.product_search_service.require_product_search_access",
    side_effect=PermissionError("Forbidden"),
)
def test_tool_forbidden_does_not_oauth_challenge(_authz) -> None:
    mcp = create_mcp_server()
    tool = mcp._tool_manager.get_tool(MCP_TOOL_SEARCH_PRODUCTS)
    result = tool.fn(page=1, page_size=10)
    dumped = result.model_dump(by_alias=True)
    assert dumped["isError"] is True
    assert dumped.get("_meta") in (None, {})
    assert dumped["content"][0]["text"] == "Forbidden"


def test_missing_oauth_scopes_detection() -> None:
    assert missing_required_oauth_scopes({"scope": "openid profile"}) == [
        "email",
        "audience-delpi",
        "mcp:tools",
    ]
    assert (
        missing_required_oauth_scopes(
            {"scope": "openid profile email audience-delpi mcp:tools"}
        )
        == []
    )


def test_token_audience_membership_exact() -> None:
    resource = CANONICAL_MCP_RESOURCE_URL
    assert token_has_exact_audience(
        {"aud": ["delpi-central", resource]},
        resource,
    )
    assert token_has_exact_audience({"aud": resource}, resource)
    assert not token_has_exact_audience({"aud": "delpi-central"}, resource)
    assert not token_has_exact_audience(
        {"aud": ["delpi-central", resource + "/"]},
        resource,
    )


@pytest.mark.asyncio
async def test_mcp_missing_bearer_challenge(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    response = await jwt_middleware(_request("/mcp"), AsyncMock())
    assert response.status_code == 401
    header = response.headers["WWW-Authenticate"]
    assert "resource_metadata=" in header
    assert 'error="invalid_token"' in header


@pytest.mark.asyncio
async def test_mcp_service_token_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=True,
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer user"}),
            AsyncMock(),
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_invalid_token_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        side_effect=ValueError("bad"),
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer bad"}),
            AsyncMock(),
        )
    assert response.status_code == 401
    assert 'error="invalid_token"' in response.headers["WWW-Authenticate"]


@pytest.mark.asyncio
async def test_mcp_wrong_issuer_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        side_effect=Exception("Invalid issuer"),
    ):
        response = await jwt_middleware(
            _request("/apps/api-delpi/mcp", {"Authorization": "Bearer x"}),
            AsyncMock(),
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_expired_token_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        side_effect=Exception("Signature has expired"),
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer expired"}),
            AsyncMock(),
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_wrong_audience_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        side_effect=Exception("Invalid audience"),
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer wrong-aud"}),
            AsyncMock(),
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_mcp_missing_scopes_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        return_value={
            "scope": "openid profile email audience-delpi",
            "sub": "u1",
            "aud": ["delpi-central", CANONICAL_MCP_RESOURCE_URL],
        },
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer tok"}),
            AsyncMock(),
        )
    assert response.status_code == 401
    assert 'error="insufficient_scope"' in response.headers["WWW-Authenticate"]


@pytest.mark.asyncio
async def test_mcp_token_without_resource_audience_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        return_value={
            "scope": "openid profile email audience-delpi mcp:tools",
            "sub": "u1",
            "aud": "delpi-central",
        },
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer only-platform"}),
            AsyncMock(),
        )
    assert response.status_code == 401
    assert 'error="invalid_token"' in response.headers["WWW-Authenticate"]
    assert "MCP resource audience" in response.headers["WWW-Authenticate"]


@pytest.mark.asyncio
async def test_mcp_valid_token_delegates_to_base(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    ok = JSONResponse(status_code=200, content={"ok": True})

    async def _base(request, call_next):
        return ok

    with patch(
        "app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=False,
    ), patch(
        "app.middleware.auth_middleware.validate_token",
        return_value={
            "scope": "openid profile email audience-delpi mcp:tools",
            "sub": "u1",
            "aud": ["delpi-central", CANONICAL_MCP_RESOURCE_URL],
        },
    ), patch(
        "app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_base,
    ):
        response = await jwt_middleware(
            _request("/mcp", {"Authorization": "Bearer good"}),
            AsyncMock(),
        )
    assert response.status_code == 200


@patch(
    "app.application.external_capabilities.product_search_auth.has_any_permission",
    return_value=False,
)
@patch("app.application.external_capabilities.product_search_auth.get_current_user")
def test_user_without_engineering_lmp_forbidden(mock_user, _perm) -> None:
    user = MagicMock()
    user.is_superadmin = False
    user.rbac_unavailable = False
    mock_user.return_value = user
    from app.application.external_capabilities.product_search_auth import (
        require_product_search_access,
    )

    with pytest.raises(PermissionError, match="Forbidden"):
        require_product_search_access()


@patch(
    "app.application.external_capabilities.product_search_auth.has_any_permission",
    return_value=True,
)
@patch("app.application.external_capabilities.product_search_auth.get_current_user")
def test_authorized_user_allowed(mock_user, _perm) -> None:
    user = MagicMock()
    user.is_superadmin = False
    user.rbac_unavailable = False
    mock_user.return_value = user
    from app.application.external_capabilities.product_search_auth import (
        require_product_search_access,
    )

    require_product_search_access()
