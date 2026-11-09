"""DÉLIA ↔ Core MCP provider registry integration tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.infrastructure.interoperability.config import (
    specialist_connections_from_core_eligible,
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.core_provider_registry import (
    CoreMcpProviderRegistryClient,
    CoreMcpProviderRegistryError,
)


class _Settings:
    mcp_timeout_seconds = 15.0
    mcp_specialist_endpoints = {
        "davi": "http://delpi-api-delpi:8000/mcp",
        "teo": "http://transformometro-api:8000/mcp",
        "vista": "",
        "caio": "",
        "clara": "",
        "suri": "",
        "eva": "",
    }
    mcp_specialist_enabled = {
        "davi": True,
        "teo": True,
        "vista": False,
        "caio": False,
        "clara": False,
        "suri": False,
        "eva": False,
    }


def test_core_eligible_enables_only_returned_providers(monkeypatch):
    monkeypatch.delenv("DELIA_MCP_DAVI_HOST_HEADER", raising=False)
    settings = _Settings()
    profiles = specialist_connections_from_core_eligible(
        settings,
        [
            {
                "providerRef": "davi",
                "endpointRef": "http://delpi-api-delpi:8000/mcp",
                "resourceClientId": "mcp-api-delpi",
                "resourceAudience": "https://minhadelpi.com.br/apps/api-delpi/mcp",
            },
            {
                "providerRef": "teo",
                "endpointRef": "http://transformometro-api:8000/mcp",
                "resourceClientId": "mcp-transformometro",
                "resourceAudience": (
                    "https://minhadelpi.com.br/apps/transformometro-api/mcp"
                ),
            },
        ],
    )
    assert profiles["davi"].enabled is True
    assert profiles["teo"].enabled is True
    assert profiles["vista"].enabled is False
    assert profiles["caio"].enabled is False
    assert profiles["clara"].enabled is False


def test_core_admits_unknown_keycloak_provider_when_identity_complete():
    settings = _Settings()
    profiles = specialist_connections_from_core_eligible(
        settings,
        [
            {
                "providerRef": "partner-ops",
                "displayName": "Partner Ops",
                "ownerRef": "partner-ops-api",
                "endpointRef": "https://partner.example/mcp",
                "authStrategyRef": "KEYCLOAK_DELEGATED",
                "resourceClientId": "mcp-partner-ops",
                "resourceAudience": "https://partner.example/mcp",
            }
        ],
    )
    assert profiles["partner-ops"].enabled is True
    assert profiles["partner-ops"].display_name == "Partner Ops"


def test_core_marks_external_oauth_unavailable_without_connection():
    settings = _Settings()
    profiles = specialist_connections_from_core_eligible(
        settings,
        [
            {
                "providerRef": "gmail-mcp",
                "displayName": "Gmail",
                "ownerRef": "google",
                "endpointRef": "https://gmail.example/mcp",
                "authStrategyRef": "EXTERNAL_OAUTH",
            }
        ],
    )
    assert profiles["gmail-mcp"].enabled is False
    assert (
        profiles["gmail-mcp"].unavailable_reason
        == "external_connection_not_implemented"
    )


def test_eligible_projection_declares_provider_approval_only_scope():
    """R1-RW05: Core eligible items must not imply user AuthZ."""
    # Contract field asserted on Core side; DÉLIA must not treat
    # providerRef presence as domain permission.
    item = {
        "providerRef": "davi",
        "authorizationScope": "provider_approval_only",
    }
    assert item["authorizationScope"] == "provider_approval_only"
    assert "permissions" not in item


def test_client_fail_closed_on_403():
    response = SimpleNamespace(status_code=403, json=lambda: {})
    http_get = MagicMock(return_value=response)
    client = CoreMcpProviderRegistryClient(
        core_api_url="http://core-api:5000",
        service_token="secret",
        timeout_seconds=2.0,
        http_get=http_get,
    )
    with pytest.raises(CoreMcpProviderRegistryError) as exc:
        client.list_eligible()
    assert "forbidden" in str(exc.value)


def test_client_fail_closed_on_missing_token():
    client = CoreMcpProviderRegistryClient(
        core_api_url="http://core-api:5000",
        service_token="",
        timeout_seconds=2.0,
        http_get=MagicMock(),
    )
    with pytest.raises(CoreMcpProviderRegistryError) as exc:
        client.list_eligible()
    assert "integrations_token_missing" in str(exc.value)


def test_client_ok_parses_items():
    response = SimpleNamespace(
        status_code=200,
        json=lambda: {"items": [{"providerRef": "davi", "endpointRef": "http://x/mcp"}]},
    )
    client = CoreMcpProviderRegistryClient(
        core_api_url="http://core-api:5000",
        service_token="secret",
        timeout_seconds=2.0,
        http_get=MagicMock(return_value=response),
    )
    items = client.list_eligible()
    assert items[0]["providerRef"] == "davi"


def test_settings_mode_unchanged_baseline():
    settings = _Settings()
    profiles = specialist_connections_from_settings(settings)
    assert profiles["davi"].enabled is True
    assert profiles["teo"].enabled is True
    assert profiles["eva"].enabled is False


def test_resolve_core_mode_fail_closed(monkeypatch):
    from app.composition.root_composer import _resolve_specialist_connections
    import logging

    settings = SimpleNamespace(
        mcp_provider_registry_mode="core",
        core_api_url="http://core-api:5000",
        core_integrations_service_token="tok",
        core_timeout_seconds=1.0,
        mcp_timeout_seconds=15.0,
        mcp_specialist_endpoints=_Settings.mcp_specialist_endpoints,
        mcp_specialist_enabled=_Settings.mcp_specialist_enabled,
    )

    class Boom(CoreMcpProviderRegistryClient):
        def list_eligible(self):
            raise CoreMcpProviderRegistryError("core_unavailable")

    monkeypatch.setattr(
        "app.composition.root_composer.CoreMcpProviderRegistryClient",
        Boom,
    )
    profiles = _resolve_specialist_connections(settings, logging.getLogger("test"))
    assert all(not p.enabled for p in profiles.values())
