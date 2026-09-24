"""DAVI live agent_directives — producer + GPT catalog + MCP discover parity."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.application.external_capabilities.catalog_service import build_gpt_catalog
from app.application.external_capabilities.davi_agent_intelligence_service import (
    DAVI_AGENT_DIRECTIVES_MAX_BYTES,
    DaviAgentIntelligenceService,
    clear_davi_agent_intelligence_cache,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.interface.mcp.branding import DAVI_MCP_INSTRUCTIONS


@pytest.fixture(autouse=True)
def _clear_caches():
    clear_davi_agent_intelligence_cache()
    clear_read_only_intent_guard_cache()
    yield
    clear_davi_agent_intelligence_cache()
    clear_read_only_intent_guard_cache()


def test_intelligence_document_is_read_only() -> None:
    doc = DaviAgentIntelligenceService.document()
    assert doc.get("read_only") is True
    assert "write_flow" not in doc
    assert "commit_now" not in doc
    assert DaviAgentIntelligenceService.version()
    for key in (
        "actions_runtime",
        "discovery",
        "execution_posture",
        "modes",
        "language",
        "anti_patterns",
        "not_exposed",
        "flows",
    ):
        assert key in doc, key


def test_agent_directives_projection_read_only_and_compact() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives.get("read_only") is True
    assert directives.get("version") == DaviAgentIntelligenceService.version()
    assert "write_flow" not in directives
    assert "commit_now" not in directives
    size = DaviAgentIntelligenceService.directives_serialized_size()
    assert size <= DAVI_AGENT_DIRECTIVES_MAX_BYTES, size


def test_gpt_catalog_exposes_same_directives() -> None:
    with patch(
        "app.application.external_capabilities.catalog_service.user_can_search_products",
        return_value=True,
    ):
        catalog = build_gpt_catalog()
    surface = catalog.get("capability_surface") or {}
    directives = surface.get("agent_directives") or {}
    assert directives == DaviAgentIntelligenceService.agent_directives()
    assert catalog.get("status") == "LEGACY_TRANSITIONAL"
    assert catalog.get("readOnly") is True
    assert set(catalog.get("operationIds") or []) == {
        "gpt_get_catalog",
        "gpt_search_products",
    }


def test_discover_exposes_same_directives(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.get_technical_actions",
        lambda: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.retrieve_eligible_actions",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "unit-test-secret",
    )
    payload = discover_delpi_information(query="estoque do produto", actor_id="user-1")
    surface = payload.get("capability_surface") or {}
    assert surface.get("agent_directives") == DaviAgentIntelligenceService.agent_directives()


def test_catalog_discover_directive_parity(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.get_technical_actions",
        lambda: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.retrieve_eligible_actions",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "unit-test-secret",
    )
    with patch(
        "app.application.external_capabilities.catalog_service.user_can_search_products",
        return_value=True,
    ):
        catalog_dirs = build_gpt_catalog()["capability_surface"]["agent_directives"]
    discover_dirs = discover_delpi_information(
        query="consulta produto", actor_id="user-1"
    )["capability_surface"]["agent_directives"]
    assert catalog_dirs["version"] == discover_dirs["version"]
    assert set(catalog_dirs.keys()) == set(discover_dirs.keys())
    assert catalog_dirs == discover_dirs


def test_write_intent_still_zero_candidates_but_directives_present(monkeypatch) -> None:
    from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
        has_explicit_write_intent,
    )

    query = "altere o estoque do produto 10080055"
    assert has_explicit_write_intent(query) is True
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.get_technical_actions",
        lambda: [],
    )
    # retrieval already zeros on write intent; still inject empty ranked
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.retrieve_eligible_actions",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "unit-test-secret",
    )
    payload = discover_delpi_information(query=query, actor_id="user-1")
    assert payload["candidate_count"] == 0
    assert payload["capability_surface"]["agent_directives"]["read_only"] is True


def test_mcp_branding_bridges_agent_directives_without_inventory() -> None:
    text = DAVI_MCP_INSTRUCTIONS
    assert "agent_directives" in text
    assert "discover_delpi_information" in text
    assert "READ-only" in text or "READ-only" in text
    assert "get_product_stock" not in text
    assert "get_product_structure" not in text
    # No mutable principle codes from JSON
    assert "TRY_TOOL_BEFORE_CLAIMING_UNAVAILABLE" not in text
    assert "DISCOVER_THEN_EXECUTE" not in text


def test_branding_and_instructions_omit_mutable_flow_keys() -> None:
    from pathlib import Path

    doc = Path(__file__).resolve().parents[1] / "docs/integrations/openai-workspace-agent-davi.md"
    marker = "## Agent instructions — canonical stable contract"
    after = doc.read_text(encoding="utf-8").split(marker, 1)[1]
    start = after.find("```text\n") + len("```text\n")
    end = after.find("\n```", start)
    paste = after[start:end] + "\n" + DAVI_MCP_INSTRUCTIONS
    doc_json = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "app/content/davi_agent_intelligence.json"
        ).read_text(encoding="utf-8")
    )
    for flow_key in (doc_json.get("flows") or {}):
        assert flow_key not in paste, flow_key
    for mode_key in (doc_json.get("modes") or {}):
        assert mode_key not in paste, mode_key


def test_discover_runtime_validates_against_declared_output_schema(monkeypatch) -> None:
    from app.interface.mcp.schemas import DiscoverDelpiInformationOutput

    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.get_technical_actions",
        lambda: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.retrieve_eligible_actions",
        lambda *a, **k: [],
    )
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "unit-test-secret",
    )
    payload = discover_delpi_information(query="estoque do produto", actor_id="user-1")
    assert "capability_surface" in payload
    model = DiscoverDelpiInformationOutput.model_validate(payload)
    assert model.capability_surface.agent_directives.get("read_only") is True
    assert model.capability_surface.agent_directives.get("version")
    # No undeclared top-level keys
    assert set(payload.keys()) == {
        "query",
        "top_k",
        "candidate_count",
        "eligible_action_count",
        "candidates",
        "capability_surface",
    }


def test_discover_output_schema_declares_capability_surface() -> None:
    from app.interface.mcp.schemas import discover_delpi_information_output_json_schema

    schema = discover_delpi_information_output_json_schema()
    assert schema.get("additionalProperties") is False
    props = schema.get("properties") or {}
    assert set(props.keys()) == {
        "query",
        "top_k",
        "candidate_count",
        "eligible_action_count",
        "candidates",
        "capability_surface",
    }
    # Nested definitions may use $defs; ensure agent_directives is reachable
    blob = json.dumps(schema)
    assert "capability_surface" in blob
    assert "agent_directives" in blob


@pytest.mark.asyncio
async def test_mcp_tools_list_and_call_discover_contract(monkeypatch) -> None:
    from app.application.external_capabilities.constants import (
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    )
    from app.interface.mcp.schemas import DiscoverDelpiInformationOutput
    from app.interface.mcp.server import create_mcp_server

    monkeypatch.setattr(
        "app.interface.mcp.server.discover_delpi_information",
        lambda **kwargs: {
            "query": kwargs.get("query") or "",
            "top_k": 5,
            "candidate_count": 0,
            "eligible_action_count": 17,
            "candidates": [],
            "capability_surface": DaviAgentIntelligenceService.capability_surface(),
        },
    )
    mcp = create_mcp_server()
    tools = await mcp.list_tools()
    names = sorted(t.name for t in tools)
    assert names == [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ]
    assert "search_products" not in names
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["surface_parity"]["mcp_tools"] == 2
    assert directives["flows"]["product_master_search"]["mcp_tools"] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert "QUICK_LOOKUP" in directives["modes"]
    assert "discover→execute" in directives["modes"]["QUICK_LOOKUP"]
    assert all("fast path" not in rule.lower() for rule in directives["discovery"]["rules"])
    discover = next(t for t in tools if t.name == MCP_TOOL_DISCOVER_DELPI_INFORMATION)
    out = discover.outputSchema or {}
    assert out.get("additionalProperties") is False
    assert "capability_surface" in (out.get("properties") or {})

    result = await mcp.call_tool(
        MCP_TOOL_DISCOVER_DELPI_INFORMATION, {"query": "estoque"}
    )
    assert result.isError is False
    structured = result.structuredContent
    assert structured is not None
    DiscoverDelpiInformationOutput.model_validate(structured)
    assert structured["capability_surface"]["agent_directives"]["read_only"] is True


def test_authority_boundary_wording_not_authz() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    authority = str(directives.get("authority") or "")
    assert "NOT AuthZ" in authority or "not AuthZ" in authority.lower()
    assert "RBAC" in authority
    assert directives.get("read_only") is True
