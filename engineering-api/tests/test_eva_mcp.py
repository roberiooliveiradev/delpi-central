"""EVA MCP V1 — contract, transport AuthN, business AuthZ and bridge.

Mirrors the TÉO surface gates over the engineering-api MCP (EVA —
Engenharia Virtual Assistida): same delpi_mcp transport, same fail-
closed negatives, same owner model (engineering-api = EVA boundary).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.conformance import McpConformanceConfig, run_mcp_conformance
from delpi_mcp.protocol import DELPI_MCP_PROTOCOL_MINIMUM
from mcp.types import LATEST_PROTOCOL_VERSION

from engineering_app.interface.mcp import tool_bridge as bridge
from engineering_app.interface.mcp.constants import (
    CANONICAL_MCP_RESOURCE_URL,
    MCP_PREDEFINED_CLIENT_ID,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from engineering_app.interface.mcp.oauth_contract import (
    EVA_MCP_SECURITY_SCHEMES,
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    missing_required_oauth_scopes,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
)
from engineering_app.interface.mcp.resource_metadata import (
    build_oauth_protected_resource_metadata,
)
from engineering_app.interface.mcp.server import create_mcp_server
from engineering_app.middleware.auth_middleware import jwt_middleware


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
            (k.lower().encode(), v.encode())
            for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    return Request(scope)


def _human_user(permissions=("engineering.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


# --- contract freeze ------------------------------------------------------


def test_contract_freeze() -> None:
    assert CANONICAL_MCP_RESOURCE_URL.endswith("/apps/engineering-api/mcp")
    assert MCP_PREDEFINED_CLIENT_ID == "mcp-engineering"
    assert set(MCP_TOOL_NAMES) == {
        "get_catalog",
        "get_engineering_home",
        "get_engineering_overview",
    }
    assert all(v in {"DISCOVERY", "READ"} for v in TOOL_CLASS.values())


def test_scopes_contract() -> None:
    assert "mcp:tools" in MCP_OAUTH_SCOPES
    schemes = EVA_MCP_SECURITY_SCHEMES
    assert schemes[0]["type"] == "oauth2"
    assert set(schemes[0]["scopes"]) == set(MCP_OAUTH_SCOPES)
    # Nenhum RBAC/permission code vaza nos schemes OAuth.
    assert "engineering.access" not in " ".join(schemes[0]["scopes"])


def test_audience_and_scope_helpers() -> None:
    resource = resolve_required_mcp_resource_audience()
    assert token_has_exact_audience({"aud": [resource]}, resource)
    assert token_has_exact_audience(
        {"aud": ["delpi-central", resource]}, resource
    )
    assert not token_has_exact_audience({"aud": ["delpi-central"]}, resource)
    assert missing_required_oauth_scopes(
        {"scope": "openid profile email mcp:tools"}
    ) == []
    assert missing_required_oauth_scopes({"scope": "openid"})


def test_resource_metadata_document() -> None:
    doc = build_oauth_protected_resource_metadata()
    assert doc["resource"] == resolve_required_mcp_resource_audience()
    assert "mcp:tools" in doc["scopes_supported"]


def test_www_authenticate_challenge() -> None:
    challenge = build_www_authenticate_challenge()
    assert challenge.startswith("Bearer ")
    assert "resource_metadata=" in challenge
    assert "mcp:tools" in challenge


# --- list_tools wire surface ----------------------------------------------


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [
        t.model_dump(mode="json", by_alias=True, exclude_none=True)
        for t in tools
    ]


def test_list_tools_surface() -> None:
    tools = _wire_tools()
    names = {t["name"] for t in tools}
    assert names == set(MCP_TOOL_NAMES)
    for tool in tools:
        assert tool["securitySchemes"][0]["type"] == "oauth2"
        assert tool["annotations"]["readOnlyHint"] is True
        assert tool["annotations"]["destructiveHint"] is False


@pytest.fixture(scope="module")
def conformance_report():
    config = McpConformanceConfig(
        name="engineering",
        expected_tool_names=tuple(MCP_TOOL_NAMES),
        expected_tool_count=len(MCP_TOOL_NAMES),
        provider_profile="openai",
        sdk_latest_protocol=LATEST_PROTOCOL_VERSION,
        protocol_minimum=DELPI_MCP_PROTOCOL_MINIMUM,
    )
    return run_mcp_conformance(_wire_tools(), config)


def test_mcp_conformance_no_failures(conformance_report):
    assert conformance_report.failures == [], conformance_report.summary()


def test_mcp_protocol_minimum(conformance_report):
    gate = next(
        r
        for r in conformance_report.results
        if r.gate == "protocol_minimum"
    )
    assert gate.status.value == "PASS"


# --- transport AuthN (middleware) -----------------------------------------


async def test_mcp_path_rejects_missing_bearer() -> None:
    request = _request("/mcp")
    call_next = AsyncMock()
    response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_missing_resource_audience() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central"],
            "scope": "openid profile email mcp:tools",
        },
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_missing_mcp_tools_scope() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": [
                "delpi-central",
                resolve_required_mcp_resource_audience(),
            ],
            "scope": "openid profile email",
        },
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_service_token() -> None:
    request = _request("/mcp", {"Authorization": "Bearer svc-token"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=True,
    ):
        response = await jwt_middleware(request, call_next)
    # Service token é proibido na superfície MCP — fail-closed.
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_accepts_valid_token_and_delegates() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": [
                "delpi-central",
                resolve_required_mcp_resource_audience(),
            ],
            "scope": "openid profile email mcp:tools",
        },
    ), patch(
        "engineering_app.middleware.auth_middleware._base_jwt_middleware",
        new_callable=AsyncMock,
    ) as base:
        base.return_value = JSONResponse({"ok": True})
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    base.assert_awaited_once()


async def test_oauth_metadata_is_public() -> None:
    request = _request(
        "/apps/engineering-api/.well-known/oauth-protected-resource"
    )
    call_next = AsyncMock(return_value=JSONResponse({"resource": "x"}))
    response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    call_next.assert_awaited_once()


# --- business AuthZ + tools ------------------------------------------------


def test_catalog_ok() -> None:
    _set_context(_human_user())
    result = bridge.tool_get_catalog()
    assert not result.is_error
    data = result.structured_content["data"]
    assert {t["name"] for t in data["tools"]} == set(MCP_TOOL_NAMES)
    assert data["write_tools"] == []
    assert all(
        p["status"] == "not_implemented"
        for p in data["planned_capabilities"]
    )
    assert all(
        t["required_permission"] == "engineering.access"
        for t in data["tools"]
    )


def test_catalog_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    result = bridge.tool_get_catalog()
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_requires_human_principal() -> None:
    _set_context(
        _human_user(principal_type="service"), "Bearer svc"
    )
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_unauthenticated_without_context() -> None:
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 401


def test_home_delegates_use_case_with_human_token(monkeypatch) -> None:
    _set_context(_human_user())
    captured = {}

    class _FakeUseCase:
        async def execute(self, ctx):
            captured["ctx"] = ctx
            return SimpleNamespace(
                model_dump=lambda: {"status": "available", "sections": []}
            )

    monkeypatch.setattr(
        bridge, "build_get_engineering_home_use_case", lambda: _FakeUseCase()
    )
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert not result.is_error
    assert captured["ctx"].access_token == "human-token"
    assert captured["ctx"].user_id == "user-1"


def test_overview_filter_validation() -> None:
    _set_context(_human_user())
    bad = asyncio.run(
        bridge.tool_get_engineering_overview(start_date="not-a-date")
    )
    assert bad.is_error
    assert bad.structured_content["status_code"] == 400

    inverted = asyncio.run(
        bridge.tool_get_engineering_overview(
            start_date="2026-10-10", end_date="2026-10-01"
        )
    )
    assert inverted.is_error

    bad_competence = asyncio.run(
        bridge.tool_get_engineering_overview(competence="2026/10")
    )
    assert bad_competence.is_error


def test_overview_delegates_filters(monkeypatch) -> None:
    _set_context(_human_user())
    captured = {}

    class _FakeUseCase:
        async def execute(self, ctx, query):
            captured["ctx"] = ctx
            captured["query"] = query
            return SimpleNamespace(
                model_dump=lambda: {"indicators": [], "status": "available"}
            )

    monkeypatch.setattr(
        bridge,
        "build_get_engineering_overview_use_case",
        lambda: _FakeUseCase(),
    )
    result = asyncio.run(
        bridge.tool_get_engineering_overview(
            start_date="2026-10-01",
            end_date="2026-10-31",
            competence="2026-10",
            branch="Matriz",
        )
    )
    assert not result.is_error
    assert captured["query"].start_date == "2026-10-01"
    assert captured["query"].branch == "Matriz"
    assert captured["ctx"].access_token == "human-token"


def test_overview_upstream_error_is_honest(monkeypatch) -> None:
    _set_context(_human_user())

    class _FailingUseCase:
        async def execute(self, ctx, query):
            raise ConnectionError("downstream down")

    monkeypatch.setattr(
        bridge,
        "build_get_engineering_overview_use_case",
        lambda: _FailingUseCase(),
    )
    result = asyncio.run(bridge.tool_get_engineering_overview())
    assert result.is_error
    assert result.structured_content["status_code"] == 502
