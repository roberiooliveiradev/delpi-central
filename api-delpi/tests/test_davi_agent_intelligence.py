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


def test_inventory_adjustment_directive_defaults_to_net_value() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    note = directives["flows"]["stock_and_supply"]["note"]
    assert "summary.net_value = surplus_value - shortage_value" in note
    assert "gross_value = surplus_value + shortage_value" in note
    assert "nature=shortage" in note
    assert "nature=surplus" in note
    assert "nunca apresente gross_value como líquido" in note


def test_product_vocabulary_directive_is_governed_and_provenanced() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    vocab = directives["product_vocabulary"]
    assert vocab["source"] == (
        "api-delpi/docs/knowledge/product-vocabulary/normative-product-terms.md"
    )
    assert "TO_INVENTORY" in vocab["normative_status"]
    rule = vocab["rule"]
    assert "TERM. PINO" in rule
    assert "equivalências não documentadas" in rule
    assert "PINO DE AJUSTE" in rule
    assert "≠ TERM. PINO" in rule
    assert "search_products" in rule


def test_product_vocabulary_source_document_exists_and_is_provenanced() -> None:
    from pathlib import Path

    doc = (
        Path(__file__).resolve().parents[1]
        / "docs/knowledge/product-vocabulary/normative-product-terms.md"
    )
    text = doc.read_text(encoding="utf-8")
    assert "Normas_Tecnicas_DELPI.md" in text
    assert "TERM. PINO" in text
    assert "corpus governado V2" in text


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
def test_authority_boundary_wording_not_authz() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    authority = str(directives.get("authority") or "")
    assert "NOT AuthZ" in authority or "not AuthZ" in authority.lower()
    assert "RBAC" in authority
    assert directives.get("read_only") is True
