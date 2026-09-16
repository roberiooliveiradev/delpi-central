"""Tests for shared external Product Master capability + MCP/plugin packaging."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
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
    VALIDATION_ERROR_CODE,
    VALIDATION_ERROR_MESSAGE,
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


def test_mcp_server_exposes_only_search_products_with_annotations() -> None:
    mcp = create_mcp_server()
    tools = mcp._tool_manager.list_tools()
    assert [t.name for t in tools] == [MCP_TOOL_SEARCH_PRODUCTS]
    tool = tools[0]
    assert tool.title == "Search DELPI products"
    annotations = tool.annotations
    assert isinstance(annotations, ToolAnnotations)
    assert annotations.readOnlyHint is True
    assert annotations.destructiveHint is False
    assert annotations.openWorldHint is False


@patch("app.interface.mcp.server.search_products")
def test_mcp_tool_returns_projected_data(mock_search) -> None:
    mock_search.return_value = {
        "items": [
            {
                "product_code": "10080160",
                "description": "PARAFUSO",
                "group_category": "0101",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
    }
    mcp = create_mcp_server()
    tool = mcp._tool_manager.get_tool(MCP_TOOL_SEARCH_PRODUCTS)
    result = tool.fn(code="1008", page=1, page_size=50)
    assert result.isError is False
    assert result.structuredContent["items"][0]["product_code"] == "10080160"
    mock_search.assert_called_once()


@patch("app.interface.mcp.server.search_products")
def test_mcp_tool_sanitizes_generic_failure(mock_search) -> None:
    mock_search.side_effect = RuntimeError("boom sql://internal")
    mcp = create_mcp_server()
    tool = mcp._tool_manager.get_tool(MCP_TOOL_SEARCH_PRODUCTS)
    with pytest.raises(RuntimeError) as exc:
        tool.fn(page=1, page_size=10)
    assert str(exc.value) == EXTERNAL_INTERNAL_ERROR_MESSAGE
    assert "sql://" not in str(exc.value)


@pytest.mark.asyncio
async def test_mcp_tools_list_contract_has_input_limits_and_typed_output() -> None:
    mcp = create_mcp_server()
    tools = await mcp.list_tools()
    assert [t.name for t in tools] == [MCP_TOOL_SEARCH_PRODUCTS]
    tool = tools[0]
    schema = tool.inputSchema
    assert schema["type"] == "object"
    assert schema.get("additionalProperties") is False
    assert schema["properties"]["page"]["minimum"] == 1
    assert schema["properties"]["page"]["default"] == 1
    assert schema["properties"]["page_size"]["minimum"] == 1
    assert schema["properties"]["page_size"]["maximum"] == PRODUCT_SEARCH_MAX_PAGE_SIZE
    assert schema["properties"]["page_size"]["default"] == PRODUCT_SEARCH_MAX_PAGE_SIZE
    assert set(schema["properties"]) == {
        "code",
        "description",
        "group_code",
        "page",
        "page_size",
    }
    assert "params" not in schema["properties"]
    assert "customer_reference" not in json.dumps(schema)

    out = tool.outputSchema
    assert out is not None
    assert out["type"] == "object"
    assert out.get("additionalProperties") is False
    out_blob = json.dumps(out)
    assert "customer_reference" not in out_blob
    for field in PRODUCT_SEARCH_RESPONSE_FIELDS:
        assert field in out_blob
    for field in ("page", "page_size", "total", "total_pages", "items"):
        assert field in out["properties"]

    assert tool.securitySchemes == [
        {"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}
    ]
    assert tool.annotations is not None
    assert tool.annotations.readOnlyHint is True


@pytest.mark.asyncio
@patch("app.interface.mcp.server.search_products")
async def test_mcp_call_tool_sanitizes_validation_errors(mock_search) -> None:
    mcp = create_mcp_server()
    for args in (
        {"page": 0, "page_size": 50},
        {"page": 1, "page_size": 0},
        {"page": 1, "page_size": 51},
        {"page": 1, "page_size": 50, "customer_reference": "x"},
        {"page": 1, "page_size": 50, "unknown": "y"},
    ):
        result = await mcp.call_tool(MCP_TOOL_SEARCH_PRODUCTS, args)
        assert result.isError is True
        text = " ".join(
            block.text for block in result.content if getattr(block, "text", None)
        )
        assert text == VALIDATION_ERROR_MESSAGE
        assert result.structuredContent == {
            "code": VALIDATION_ERROR_CODE,
            "message": VALIDATION_ERROR_MESSAGE,
        }
        blob = str(result)
        assert "pydantic" not in blob.lower()
        assert "errors.pydantic.dev" not in blob
        assert "ValidationError" not in blob
        assert "greater_than_equal" not in blob
        assert "traceback" not in blob.lower()
    mock_search.assert_not_called()


@pytest.mark.asyncio
@patch("app.interface.mcp.server.search_products")
async def test_mcp_call_tool_positive_pagination(mock_search) -> None:
    mock_search.return_value = {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
    }
    mcp = create_mcp_server()
    result = await mcp.call_tool(
        MCP_TOOL_SEARCH_PRODUCTS, {"page": 1, "page_size": 50}
    )
    assert result.isError is False
    mock_search.assert_called_once()


def test_mcp_tool_fn_returns_safe_validation_error() -> None:
    mcp = create_mcp_server()
    tool = mcp._tool_manager.get_tool(MCP_TOOL_SEARCH_PRODUCTS)
    result = tool.fn(page=0, page_size=50)
    assert result.isError is True
    assert result.structuredContent["code"] == VALIDATION_ERROR_CODE
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
    assert "search_products" in skill
    assert "RBAC" not in skill
    assert "ENGINEERING_LMP" not in skill
