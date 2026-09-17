"""TÉO MCP OAuth contract + tool parity (code-level; not live Keycloak)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

from tm_app.application.gpt_actions.openapi_builder import GPT_ACTIONS_OPERATION_IDS
from tm_app.interface.mcp.constants import (
    CANONICAL_MCP_RESOURCE_URL,
    GPT_ACTIONS_LIFECYCLE,
    MCP_PREDEFINED_CLIENT_ID,
    MCP_TOOL_NAMES,
    TEO_MCP_SURFACE,
    TOOL_CLASS,
    TOOL_TO_GPT_OPERATION,
)
from tm_app.interface.mcp.oauth_contract import (
    KEYCLOAK_INTERNAL_AUDIENCE_CLIENT_SCOPE,
    MCP_OAUTH_SCOPES,
    MCP_RESOURCE_BINDING_SCOPE,
    TEO_MCP_SECURITY_SCHEMES,
    build_www_authenticate_challenge,
    missing_required_oauth_scopes,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
)
from tm_app.interface.mcp.resource_metadata import build_oauth_protected_resource_metadata
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.middleware.auth_middleware import jwt_middleware


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


def test_contract_freeze_full_crud() -> None:
    assert TEO_MCP_SURFACE == "FULL_CRUD"
    assert MCP_PREDEFINED_CLIENT_ID == "mcp-transformometro"
    assert CANONICAL_MCP_RESOURCE_URL.endswith("/apps/transformometro-api/mcp")
    assert GPT_ACTIONS_LIFECYCLE == "LEGACY_TRANSITIONAL_BRIDGE"
    assert MCP_RESOURCE_BINDING_SCOPE == "mcp:tools"
    assert KEYCLOAK_INTERNAL_AUDIENCE_CLIENT_SCOPE == "audience-delpi"
    assert MCP_OAUTH_SCOPES == ("openid", "profile", "email", "mcp:tools")
    assert "audience-delpi" not in MCP_OAUTH_SCOPES


def test_tool_parity_with_gpt_actions_operation_ids() -> None:
    assert len(MCP_TOOL_NAMES) == 20
    assert set(TOOL_TO_GPT_OPERATION.values()) == set(GPT_ACTIONS_OPERATION_IDS)
    assert set(TOOL_CLASS) == set(MCP_TOOL_NAMES)
    assert TOOL_CLASS["validate_improvement_package"] == "PREPARE"
    assert TOOL_CLASS["create_record"] == "ACT"
    assert TOOL_CLASS["get_catalog"] == "READ"
    # FULL CRUD must include writes
    assert any(TOOL_CLASS[n] == "ACT" for n in MCP_TOOL_NAMES)
    assert any(TOOL_CLASS[n] == "PREPARE" for n in MCP_TOOL_NAMES)


def test_security_schemes_have_no_rbac_codes() -> None:
    blob = json.dumps(TEO_MCP_SECURITY_SCHEMES)
    assert "transformometro.view" not in blob
    assert "audience-delpi" not in blob
    assert "mcp:tools" in blob


def test_list_tools_exposes_twenty_full_crud_tools() -> None:
    mcp = create_mcp_server()
    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert len(names) == 20
    assert set(names) == set(MCP_TOOL_NAMES)
    for tool in tools:
        assert tool.securitySchemes == TEO_MCP_SECURITY_SCHEMES  # type: ignore[attr-defined]


def test_audience_and_scope_helpers() -> None:
    claims = {
        "aud": ["delpi-central", CANONICAL_MCP_RESOURCE_URL],
        "scope": "openid profile email mcp:tools",
    }
    assert token_has_exact_audience(claims, CANONICAL_MCP_RESOURCE_URL)
    assert missing_required_oauth_scopes(claims) == []
    assert missing_required_oauth_scopes({"scope": "openid"}) == [
        "profile",
        "email",
        "mcp:tools",
    ]


def test_resource_metadata_document() -> None:
    with patch.dict(
        "os.environ",
        {
            "PUBLIC_BASE_URL": "https://minhadelpi.com.br",
            "KEYCLOAK_ISSUER": "https://auth.example/realms/delpi",
        },
        clear=False,
    ):
        doc = build_oauth_protected_resource_metadata()
    assert doc["resource"] == CANONICAL_MCP_RESOURCE_URL
    assert "mcp:tools" in doc["scopes_supported"]
    assert doc["authorization_servers"] == ["https://auth.example/realms/delpi"]


def test_www_authenticate_challenge_mentions_metadata() -> None:
    challenge = build_www_authenticate_challenge(
        error="invalid_token",
        error_description="Authentication required",
    )
    assert challenge.startswith("Bearer ")
    assert "resource_metadata=" in challenge
    assert "mcp:tools" in challenge


@pytest.mark.asyncio
async def test_mcp_path_rejects_missing_bearer() -> None:
    request = _request("/mcp")
    call_next = AsyncMock()
    response = await jwt_middleware(request, call_next)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_mcp_path_rejects_missing_resource_audience() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "tm_app.middleware.auth_middleware.validate_token",
        return_value={"aud": ["delpi-central"], "scope": "openid profile email mcp:tools"},
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_mcp_path_rejects_missing_mcp_tools_scope() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "tm_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central", resolve_required_mcp_resource_audience()],
            "scope": "openid profile email",
        },
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_mcp_path_accepts_valid_token_and_delegates() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "tm_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central", resolve_required_mcp_resource_audience()],
            "scope": "openid profile email mcp:tools",
        },
    ), patch(
        "tm_app.middleware.auth_middleware._base_jwt_middleware",
        new_callable=AsyncMock,
    ) as base:
        base.return_value = JSONResponse({"ok": True})
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    base.assert_awaited_once()


@pytest.mark.asyncio
async def test_oauth_metadata_is_public() -> None:
    request = _request("/.well-known/oauth-protected-resource")
    call_next = AsyncMock(return_value=JSONResponse({"resource": "x"}))
    response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    call_next.assert_awaited_once()


def test_manage_evidence_requires_confirm_delete_flag_in_description() -> None:
    mcp = create_mcp_server()
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    desc = tools["manage_evidence"].description or ""
    assert "confirm_delete" in desc
    commit = tools["commit_improvement_package"].description or ""
    assert "validate_improvement_package" in commit
