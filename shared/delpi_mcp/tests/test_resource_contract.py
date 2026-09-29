"""S1 unit tests for the shared MCP OAuth / RFC 9728 resource contract."""

from __future__ import annotations

import json

import pytest

from delpi_mcp.resource_contract import (
    MCP_TRANSPORT_SCOPES,
    McpResourceConfig,
    build_protected_resource_metadata,
    build_www_authenticate_challenge,
    build_www_authenticate_meta,
    extract_token_audiences,
    extract_token_scopes,
    mcp_allowed_hosts_and_origins,
    missing_required_scopes,
    protected_resource_metadata_url,
    token_has_required_audience,
)

RESOURCE = "https://minhadelpi.com.br/apps/example/mcp"
METADATA_URL = "https://minhadelpi.com.br/apps/example/.well-known/oauth-protected-resource"


def _config(**overrides) -> McpResourceConfig:
    base = {
        "resolve_resource_url": lambda: RESOURCE,
        "resolve_authorization_server": lambda: "https://keycloak.example/realms/delpi",
    }
    base.update(overrides)
    return McpResourceConfig(**base)


class TestChallenge:
    def test_basic_space_separated(self):
        challenge = build_www_authenticate_challenge(
            realm="example-mcp",
            metadata_url=METADATA_URL,
            scope_value="openid profile email mcp:tools",
        )
        assert challenge == (
            'Bearer realm="example-mcp" '
            f'resource_metadata="{METADATA_URL}" '
            'scope="openid profile email mcp:tools"'
        )

    def test_error_fields_appended_after_scope(self):
        challenge = build_www_authenticate_challenge(
            realm="example-mcp",
            metadata_url=METADATA_URL,
            scope_value="mcp:tools",
            error="invalid_token",
            error_description="Authentication required",
        )
        assert challenge.endswith(
            'scope="mcp:tools" error="invalid_token" '
            'error_description="Authentication required"'
        )

    def test_error_description_escapes_double_quotes(self):
        challenge = build_www_authenticate_challenge(
            realm="r",
            metadata_url=METADATA_URL,
            scope_value="s",
            error="invalid_token",
            error_description='bad "token" value',
        )
        assert "error_description=\"bad 'token' value\"" in challenge

    def test_scope_omitted_when_empty(self):
        challenge = build_www_authenticate_challenge(
            realm="r", metadata_url=METADATA_URL, scope_value=""
        )
        assert "scope=" not in challenge

    def test_scope_last_and_comma_separator(self):
        challenge = build_www_authenticate_challenge(
            realm="mcp",
            metadata_url=METADATA_URL,
            scope_value="mcp:tools",
            separator=", ",
            scope_last=True,
            default_error=("invalid_token", "Missing or invalid access token"),
        )
        assert challenge == (
            'Bearer realm="mcp", '
            f'resource_metadata="{METADATA_URL}", '
            'error="invalid_token", '
            'error_description="Missing or invalid access token", '
            'scope="mcp:tools"'
        )

    def test_explicit_error_overrides_default(self):
        challenge = build_www_authenticate_challenge(
            realm="mcp",
            metadata_url=METADATA_URL,
            scope_value="mcp:tools",
            separator=", ",
            scope_last=True,
            default_error=("invalid_token", "Missing or invalid access token"),
            error="insufficient_scope",
            error_description="Need mcp:tools",
        )
        assert 'error="insufficient_scope"' in challenge
        assert "Missing or invalid" not in challenge


class TestAudience:
    def test_string_aud(self):
        assert token_has_required_audience({"aud": RESOURCE}, RESOURCE)

    def test_array_aud(self):
        assert token_has_required_audience({"aud": ["x", RESOURCE]}, RESOURCE)

    def test_additional_audiences_allowed(self):
        claims = {"aud": [RESOURCE, "https://other/resource"]}
        assert token_has_required_audience(claims, RESOURCE)

    def test_wrong_audience_fails(self):
        assert not token_has_required_audience({"aud": "https://other"}, RESOURCE)

    def test_missing_aud_fails(self):
        assert not token_has_required_audience({}, RESOURCE)

    def test_null_aud_fails(self):
        assert not token_has_required_audience({"aud": None}, RESOURCE)

    def test_empty_expected_fails_closed(self):
        assert not token_has_required_audience({"aud": RESOURCE}, "")

    def test_exact_match_no_slash_rewrite(self):
        assert not token_has_required_audience({"aud": RESOURCE}, RESOURCE + "/")


class TestScopes:
    def test_extract_scope_string(self):
        assert extract_token_scopes({"scope": "openid mcp:tools"}) == {
            "openid",
            "mcp:tools",
        }

    def test_extract_scp_and_list(self):
        assert extract_token_scopes({"scp": ["a", "b"]}) == {"a", "b"}

    def test_missing_required_in_order(self):
        missing = missing_required_scopes(
            {"scope": "openid email"}, MCP_TRANSPORT_SCOPES
        )
        assert missing == ["profile", "mcp:tools"]

    def test_all_present(self):
        claims = {"scope": "openid profile email mcp:tools extra"}
        assert missing_required_scopes(claims, MCP_TRANSPORT_SCOPES) == []


class TestMetadata:
    def test_required_fields(self):
        doc = build_protected_resource_metadata(_config())
        assert doc["resource"] == RESOURCE
        assert doc["authorization_servers"] == ["https://keycloak.example/realms/delpi"]
        assert doc["scopes_supported"] == list(MCP_TRANSPORT_SCOPES)
        assert doc["bearer_methods_supported"] == ["header"]

    def test_no_issuer_yields_empty_list(self):
        doc = build_protected_resource_metadata(
            _config(resolve_authorization_server=lambda: None)
        )
        assert doc["authorization_servers"] == []

    def test_optional_signing_alg_only_when_configured(self):
        assert "resource_signing_alg_values_supported" not in (
            build_protected_resource_metadata(_config())
        )
        doc = build_protected_resource_metadata(
            _config(resource_signing_alg_values_supported=("RS256",))
        )
        assert doc["resource_signing_alg_values_supported"] == ["RS256"]

    def test_documentation_field(self):
        doc = build_protected_resource_metadata(
            _config(resource_documentation="https://docs.example/x")
        )
        assert doc["resource_documentation"] == "https://docs.example/x"

    def test_json_serializable(self):
        json.dumps(build_protected_resource_metadata(_config()))

    def test_metadata_url_strips_mcp(self):
        assert protected_resource_metadata_url(RESOURCE) == METADATA_URL

    def test_metadata_url_without_mcp_suffix(self):
        assert protected_resource_metadata_url(
            "https://h/apps/x"
        ) == "https://h/apps/x/.well-known/oauth-protected-resource"


class TestMetaEnvelope:
    def test_list_shape(self):
        meta = build_www_authenticate_meta("Bearer x", wrap_in_list=True)
        assert meta == {"mcp/www_authenticate": ["Bearer x"]}

    def test_string_shape(self):
        meta = build_www_authenticate_meta("Bearer x", wrap_in_list=False)
        assert meta == {"mcp/www_authenticate": "Bearer x"}


class TestAllowedHostsAndOrigins:
    def test_defaults_without_base(self):
        hosts, origins = mcp_allowed_hosts_and_origins(None)
        assert "localhost:*" in hosts
        assert "https://chatgpt.com" in origins

    def test_derives_host_and_origin(self):
        hosts, origins = mcp_allowed_hosts_and_origins("https://minhadelpi.com.br")
        assert "minhadelpi.com.br" in hosts
        assert "minhadelpi.com.br:*" in hosts
        assert "https://minhadelpi.com.br" in origins

    def test_port_preserved(self):
        hosts, origins = mcp_allowed_hosts_and_origins("http://127.0.0.1:8080")
        assert "http://127.0.0.1:8080" in origins


class TestMetadataRouter:
    @pytest.fixture()
    def client(self):
        pytest.importorskip("fastapi")
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from delpi_mcp.resource_contract import mcp_metadata_router

        app = FastAPI()
        app.include_router(
            mcp_metadata_router(
                _config(
                    metadata_paths=(
                        "/.well-known/oauth-protected-resource",
                        "/.well-known/oauth-protected-resource/mcp",
                    )
                )
            )
        )
        return TestClient(app)

    def test_alias_paths_serve_same_document(self, client):
        base = client.get("/.well-known/oauth-protected-resource")
        alias = client.get("/.well-known/oauth-protected-resource/mcp")
        assert base.status_code == 200
        assert alias.status_code == 200
        assert base.json() == alias.json()
        assert base.json()["resource"] == RESOURCE
