"""Structural checks for DAVI Workspace Agent canonical Instructions (docs)."""

from __future__ import annotations

from pathlib import Path

_DOC = (
    Path(__file__).resolve().parents[1]
    / "docs/integrations/openai-workspace-agent-davi.md"
)


def _canonical_block() -> str:
    text = _DOC.read_text(encoding="utf-8")
    marker = "## Agent instructions — canonical stable contract"
    assert marker in text
    after = text.split(marker, 1)[1]
    # First fenced text block after the section heading.
    start = after.find("```text\n")
    assert start >= 0
    start += len("```text\n")
    end = after.find("\n```", start)
    assert end > start
    return after[start:end]


def test_canonical_agent_instructions_contain_stable_protocol() -> None:
    block = _canonical_block()
    for required in (
        "discover_delpi_information",
        "execute_delpi_information",
        "Product Master",
        "somente leitura",
        "backend canônico",
        "candidate_token",
        "agent_directives",
        "capability_surface",
    ):
        assert required in block, required


def test_canonical_agent_instructions_omit_dynamic_inventory() -> None:
    block = _canonical_block().lower()
    # No current eligible count / business capability catalog in the prompt.
    assert "davi_eligible_read" not in block
    assert "eligible_read = 7" not in block
    assert "get_product_stock" not in block
    assert "get_product_suppliers" not in block
    assert "get_product_customers" not in block
    assert "get_product_purchases" not in block
    assert "get_product_structure" not in block
    assert "get_product_production_status" not in block
    assert "get_product_factory_status" not in block
    assert "get_product_structure_exclusivity" not in block
    assert "get_product_shipping_status" not in block
    assert "eligible_read = 10" not in block
    # No hardcoded global field allowlist.
    assert "product_code" not in block
    assert "group_category" not in block
    # No stale negative family bans.
    assert "nunca obtenha estoque" not in block
    assert "nunca obtenha fornecedor" not in block
    assert "capability disponível nesta versão" not in block


def test_canonical_agent_instructions_omit_mutable_intelligence_keys() -> None:
    """Leak gate: mutable JSON sections must not be pasted into Agent Instructions."""
    block = _canonical_block().lower()
    for forbidden in (
        "try_tool_before_claiming_unavailable",
        "discover_then_execute",
        "authoritative_tool_data_only",
        "quick_lookup",
        "multi_source_reconcile",
        "explain_gap",
        "product_master_search",
        "stock_and_supply",
        "structure_bom",
        "write_request",
        "persona_bridge",
        "surface_parity",
    ):
        assert forbidden not in block, forbidden


def test_doc_marks_historical_preview_and_pending_studio_sync() -> None:
    text = _DOC.read_text(encoding="utf-8")
    assert "HISTORICAL / SUPERSEDED" in text
    assert "AGENT_STUDIO_SYNC = PENDING_MANUAL_SYNC" in text
    assert "READ capability promotion behind the same discover/execute contract" in text
    assert "NO Agent Instruction change required" in text
