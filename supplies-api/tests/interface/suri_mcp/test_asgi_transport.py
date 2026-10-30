"""ASGI-level transport tests — real HTTP through the sibling SURI app.

Covers: public surfaces, fail-closed auth on the MCP data surface,
/mcp → /mcp/ rewrite without redirect, and the DNS-rebinding protection
settings wired into the mounted MCP transport.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.interfaces.mcp import asgi as mcp_asgi
from app.interfaces.mcp import server as mcp_server

METADATA_URL = (
    "https://supplies.example/apps/supplies-api"
    "/.well-known/oauth-protected-resource"
)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://sso.example/realms/delpi")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://supplies.example")
    monkeypatch.delenv("MCP_RESOURCE_URL", raising=False)
    return TestClient(mcp_asgi.app, raise_server_exceptions=False)


class TestPublicSurface:
    def test_healthz_public(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["service"] == "supplies-mcp"

    def test_protected_resource_metadata_public(self, client):
        resp = client.get("/.well-known/oauth-protected-resource")
        assert resp.status_code == 200
        body = resp.json()
        assert (
            body["resource"]
            == "https://supplies.example/apps/supplies-api/mcp"
        )
        assert body["authorization_servers"] == [
            "https://sso.example/realms/delpi"
        ]

    def test_no_business_routes_exposed(self, client):
        resp = client.get("/openapi.json")
        if resp.status_code == 200:
            paths = resp.json().get("paths", {})
            assert not any("purchase" in p for p in paths)


class TestMcpDataPathFailClosed:
    def test_missing_bearer_401_with_challenge(self, client):
        resp = client.post("/mcp", json={})
        assert resp.status_code == 401
        www = resp.headers.get("www-authenticate", "")
        assert www.startswith("Bearer ")
        assert 'realm="suri-mcp"' in www
        assert f'resource_metadata="{METADATA_URL}"' in www
        assert "mcp:tools" in www

    def test_malformed_bearer_401(self, client):
        resp = client.post(
            "/mcp", json={}, headers={"Authorization": "NotBearer x"}
        )
        assert resp.status_code == 401

    def test_get_on_mcp_not_public(self, client):
        resp = client.get("/mcp")
        assert resp.status_code == 401

    def test_no_redirect_on_exact_mcp(self, client):
        # The path rewrite must NOT answer with 307/308 redirects —
        # connectors drop auth headers on redirects
        resp = client.post("/mcp", json={}, follow_redirects=False)
        assert resp.status_code not in (307, 308)


class TestDnsRebindingProtection:
    """The host/origin allowlist lives inside the mounted MCP transport
    (SDK TransportSecuritySettings) — asserted at the settings level."""

    def test_protection_enabled_with_allowlists(self, monkeypatch):
        monkeypatch.setenv("PUBLIC_BASE_URL", "https://supplies.example")
        settings = mcp_server.suri_mcp_transport_security()
        assert settings.enable_dns_rebinding_protection is True
        assert any("supplies.example" in h for h in settings.allowed_hosts)
        assert any(
            "localhost" in h for h in settings.allowed_hosts
        )
        assert "https://chatgpt.com" in settings.allowed_origins
        assert "https://chat.openai.com" in settings.allowed_origins
        assert not any(
            "attacker" in o for o in settings.allowed_origins
        )
