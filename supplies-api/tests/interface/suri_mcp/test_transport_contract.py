"""SURI transport/OAuth contract tests (S3): challenge, audience,
protected-resource metadata, scope/aud extraction and server wire shape."""

from __future__ import annotations

import asyncio

from app.interfaces.mcp.constants import (
    CANONICAL_MCP_RESOURCE_URL,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from app.interfaces.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    missing_required_oauth_scopes,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
)
from app.interfaces.mcp.resource_metadata import (
    build_oauth_protected_resource_metadata,
)
from app.interfaces.mcp.server import suri_mcp_server


class TestOAuthContract:
    def test_required_scopes_frozen(self):
        assert MCP_OAUTH_SCOPES == (
            "openid",
            "profile",
            "email",
            "mcp:tools",
        )

    def test_audience_resolution_order(self, monkeypatch):
        monkeypatch.setenv("MCP_RESOURCE_URL", "https://x.example/mcp")
        assert (
            resolve_required_mcp_resource_audience()
            == "https://x.example/mcp"
        )
        monkeypatch.delenv("MCP_RESOURCE_URL")
        monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
        assert (
            resolve_required_mcp_resource_audience()
            == "https://minhadelpi.com.br/apps/supplies-api/mcp"
        )
        monkeypatch.delenv("PUBLIC_BASE_URL")
        assert (
            resolve_required_mcp_resource_audience()
            == CANONICAL_MCP_RESOURCE_URL
        )

    def test_challenge_shape(self, monkeypatch):
        monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
        challenge = build_www_authenticate_challenge(
            error="invalid_token", error_description="Authentication required"
        )
        assert challenge.startswith('Bearer realm="suri-mcp"')
        assert (
            'resource_metadata="https://minhadelpi.com.br/apps/supplies-api/'
            '.well-known/oauth-protected-resource"' in challenge
        )
        assert 'scope="openid profile email mcp:tools"' in challenge
        assert 'error="invalid_token"' in challenge

    def test_exact_audience_membership(self):
        expected = "https://minhadelpi.com.br/apps/supplies-api/mcp"
        assert token_has_exact_audience({"aud": [expected, "other"]}, expected)
        assert not token_has_exact_audience({"aud": ["other"]}, expected)
        assert not token_has_exact_audience({}, expected)
        # sibling resource must not bind
        assert not token_has_exact_audience(
            {"aud": "https://minhadelpi.com.br/apps/other-api/mcp"}, expected
        )

    def test_missing_scopes(self):
        assert missing_required_oauth_scopes(
            {"scope": "openid profile email"}
        ) == ["mcp:tools"]
        assert missing_required_oauth_scopes(
            {"scope": "openid profile email mcp:tools"}
        ) == []


class TestProtectedResourceMetadata:
    def test_document_shape(self, monkeypatch):
        monkeypatch.setenv(
            "PUBLIC_BASE_URL", "https://minhadelpi.com.br"
        )
        monkeypatch.setenv(
            "KEYCLOAK_ISSUER", "https://sso.example/realms/delpi"
        )
        doc = build_oauth_protected_resource_metadata()
        assert doc["resource"].endswith("/apps/supplies-api/mcp")
        assert doc["authorization_servers"] == [
            "https://sso.example/realms/delpi"
        ]
        assert doc["scopes_supported"] == list(MCP_OAUTH_SCOPES)
        assert doc["bearer_methods_supported"] == ["header"]


class TestServerWire:
    def test_list_tools_wire_contract(self):
        tools = asyncio.run(suri_mcp_server.list_tools())
        assert {t.name for t in tools} == set(MCP_TOOL_NAMES)
        for tool in tools:
            meta = tool.meta or {}
            assert meta["delpi/toolClass"] == TOOL_CLASS[tool.name]
            schemes = getattr(tool, "securitySchemes", None)
            assert schemes and schemes[0]["type"] == "oauth2"
            assert tool.input_schema.get("type") == "object"
            if TOOL_CLASS[tool.name] == "ACT":
                # rev.3 — execute is a governed write: not read-only, not
                # destructive, idempotent hint declared.
                assert tool.annotations.read_only_hint is False
                assert tool.annotations.destructive_hint is not True
                assert tool.annotations.idempotent_hint is True
            else:
                assert tool.annotations.read_only_hint is True
                assert tool.annotations.destructive_hint is not True

    def test_act_surface_is_closed(self):
        # Only the governed execute tool carries the ACT class — no
        # PREPARE tools and no destructive registrations in rev.3.
        act_tools = {
            name for name, kind in TOOL_CLASS.items() if kind == "ACT"
        }
        assert act_tools == {"execute"}
        assert all(
            TOOL_CLASS[name]
            in {"DISCOVERY", "READ", "ANALYSIS", "ACT"}
            for name in MCP_TOOL_NAMES
        )
