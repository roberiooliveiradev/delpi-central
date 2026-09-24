"""Tests for shared external Product Master capability + MCP/plugin packaging."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    MCP_TOOL_SEARCH_PRODUCTS,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
    PRODUCT_SEARCH_RESPONSE_FIELDS,
)
from app.application.external_capabilities.product_search_projection import (
    project_product_search_item,
)
from app.application.external_capabilities.product_search_service import (
    normalize_product_search_pagination,
    search_products,
)
from app.application.models.page import Page
from app.interface.mcp.resource_metadata import (
    build_oauth_protected_resource_metadata,
    www_authenticate_challenge,
)
from app.interface.mcp.schemas import (
    SearchProductsInput,
)
from app.interface.mcp.server import (
    create_mcp_server,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "integrations" / "openai-plugin"


def test_allowlist_fail_closed_for_unknown_fields() -> None:
    projected = project_product_search_item(
        {
            "code": "1",
            "description": "d",
            "group_code": "g",
            "brand_new_secret_field": "leak",
            "customer_reference": "x",
        }
    )
    assert set(projected.keys()) == set(PRODUCT_SEARCH_RESPONSE_FIELDS)
    assert "brand_new_secret_field" not in projected
    assert "customer_reference" not in projected


def test_pagination_limits() -> None:
    assert normalize_product_search_pagination(page=0, page_size=0) == (1, 1)
    assert normalize_product_search_pagination(page=-5, page_size=999) == (
        1,
        PRODUCT_SEARCH_MAX_PAGE_SIZE,
    )
    assert normalize_product_search_pagination(page=3, page_size=10) == (3, 10)


def test_search_products_input_rejects_customer_reference_and_unknown() -> None:
    with pytest.raises(ValidationError):
        SearchProductsInput.model_validate({"customer_reference": "x"})
    with pytest.raises(ValidationError):
        SearchProductsInput.model_validate({"page_size": 51})
    with pytest.raises(ValidationError):
        SearchProductsInput.model_validate({"page": 0})
    with pytest.raises(ValidationError):
        SearchProductsInput.model_validate({"unknown": "nope"})


@patch("app.application.external_capabilities.product_search_service.require_product_search_access")
def test_search_products_reuses_use_case_and_authz(mock_authz) -> None:
    product = MagicMock()
    product.to_dict.return_value = {
        "code": "A",
        "description": "B",
        "group_code": "C",
        "customer_reference": "no",
    }
    mock_uc = MagicMock()
    mock_uc.execute.return_value = Page(items=[product], total=1, page=1, page_size=50)

    result = search_products(
        search_use_case=mock_uc,
        code="A",
        page=1,
        page_size=50,
        enforce_authz=True,
    )
    mock_authz.assert_called_once()
    assert result["items"][0]["product_code"] == "A"
    assert "customer_reference" not in result["items"][0]
    assert mock_uc.execute.call_args[0][0].customer_reference is None


def test_product_search_service_does_not_import_composition_root() -> None:
    """Regression: Application must not depend on Composition Root for search_products."""
    from pathlib import Path

    source = Path(
        "app/application/external_capabilities/product_search_service.py"
    )
    # Resolve relative to api-delpi package root (tests/ sibling of app/)
    path = Path(__file__).resolve().parents[1] / source
    text = path.read_text(encoding="utf-8")
    assert "app.composition" not in text
    assert "product_composer" not in text
    assert "build_search_products_use_case" not in text


def test_mcp_server_exposes_only_discover_execute_with_annotations() -> None:
    mcp = create_mcp_server()
    tools = mcp._tool_manager.list_tools()
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert MCP_TOOL_SEARCH_PRODUCTS not in [t.name for t in tools]
    for tool in tools:
        annotations = tool.annotations
        assert isinstance(annotations, ToolAnnotations)
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.openWorldHint is False


@pytest.mark.asyncio
async def test_mcp_tools_list_contract_has_discover_execute_schemas() -> None:
    mcp = create_mcp_server()
    tools = await mcp.list_tools()
    assert [t.name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    discover = tools[0]
    schema = discover.inputSchema
    assert schema["type"] == "object"
    assert schema.get("additionalProperties") is False
    assert "query" in schema["properties"]
    assert discover.securitySchemes == [
        {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
    ]
    assert discover.annotations is not None
    assert discover.annotations.readOnlyHint is True

    execute = tools[1]
    assert "candidate_token" in execute.inputSchema["properties"]
    assert execute.securitySchemes == discover.securitySchemes


@pytest.mark.asyncio
async def test_mcp_call_tool_sanitizes_discover_validation_errors() -> None:
    mcp = create_mcp_server()
    result = await mcp.call_tool("discover_delpi_information", {"query": ""})
    assert result.isError is True
    text = " ".join(
        block.text for block in result.content if getattr(block, "text", None)
    )
    assert text
    assert "pydantic" not in str(result).lower()


@pytest.mark.asyncio
async def test_mcp_call_tool_sanitizes_execute_validation_errors() -> None:
    mcp = create_mcp_server()
    result = await mcp.call_tool("execute_delpi_information", {"candidate_token": ""})
    assert result.isError is True
    assert "pydantic" not in str(result).lower()


def test_oauth_resource_metadata_shape(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://minhadelpi.com.br/auth/realms/delpi")
    monkeypatch.delenv("MCP_RESOURCE_URL", raising=False)
    doc = build_oauth_protected_resource_metadata()
    assert doc["resource"] == "https://minhadelpi.com.br/apps/api-delpi/mcp"
    assert doc["authorization_servers"] == [
        "https://minhadelpi.com.br/auth/realms/delpi"
    ]
    assert "openid" in doc["scopes_supported"]
    assert "mcp:tools" in doc["scopes_supported"]
    assert "audience-delpi" not in doc["scopes_supported"]
    challenge = www_authenticate_challenge(
        error="invalid_token",
        error_description="Authentication required",
    )
    assert "resource_metadata=" in challenge
    assert "Bearer" in challenge
    assert 'error="invalid_token"' in challenge
    assert "mcp:tools" in challenge
    assert "audience-delpi" not in challenge


def test_plugin_package_schemas_and_skill() -> None:
    plugin = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((PLUGIN_ROOT / "mcp.json").read_text(encoding="utf-8"))
    skill = (PLUGIN_ROOT / "skills" / "api-delpi" / "SKILL.md").read_text(encoding="utf-8")

    assert plugin["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert plugin["name"] == "api-delpi"
    assert "DAVI" in plugin["description"]
    assert "Write" not in plugin.get("keywords", [])
    blob = json.dumps(plugin) + json.dumps(mcp) + skill
    assert "client_secret" not in blob.lower()
    assert "Bearer ey" not in blob

    assert mcp["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    server = mcp["mcpServers"]["api-delpi"]
    assert server["type"] == "streamable-http"
    assert server["url"] == "https://minhadelpi.com.br/apps/api-delpi/mcp"
    assert "localhost" not in server["url"]

    assert skill.startswith("---")
    assert "name: api-delpi" in skill
    assert "DAVI" in skill
    assert "discover_delpi_information" in skill
    assert "execute_delpi_information" in skill
    assert "RBAC" not in skill
    assert "ENGINEERING_LMP" not in skill
