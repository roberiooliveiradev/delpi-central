"""MCP3 — VISTA client migration artifacts.

Asserts the MCP-primary client configuration artifacts are coherent with the
frozen MCP server surface: parity map names match real registered tools,
write_flow_mcp carries the governed envelope semantics, and the MCP builder
instructions variant stays inside budget without leaking mutable directives.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "gpt-actions"
    / "specialist-instructions.md"
)
INTELLIGENCE = (
    Path(__file__).resolve().parents[1]
    / "tv_app"
    / "content"
    / "vista_agent_intelligence.json"
)
PROJECT_TARGET_LIMIT = 3500

from tv_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
from tv_app.interface.mcp.server import create_mcp_server


def _mcp_instructions_block() -> str:
    text = DOC.read_text(encoding="utf-8")
    heading = "## Instructions MCP (colar quando o conector for MCP)"
    start = text.index("```text\n", text.index(heading)) + len("```text\n")
    end = text.index("\n```", start)
    return text[start:end]


def _actions_instructions_block() -> str:
    text = DOC.read_text(encoding="utf-8")
    heading = "## Instructions (colar no GPT Builder)"
    start = text.index("```text\n", text.index(heading)) + len("```text\n")
    end = text.index("\n```", start)
    return text[start:end]


# ---------------------------------------------------------------------------
# Surface unchanged — MCP3 adds zero server changes
# ---------------------------------------------------------------------------


def test_mcp_surface_still_exactly_eight():
    tools = asyncio.run(create_mcp_server().list_tools())
    assert {t.name for t in tools} == set(MCP_TOOL_NAMES)
    assert len(tools) == 8
    assert TOOL_CLASS["prepare_change"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"


# ---------------------------------------------------------------------------
# Intelligence JSON — parity map + MCP write flow
# ---------------------------------------------------------------------------


def test_surface_parity_map_matches_registered_tools():
    intel = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    parity = intel["surface_parity"]
    assert parity["principle"] == "SAME_DISPATCH_BOTH_TRANSPORTS"
    mapping = parity["parity_map"]
    # Every MCP name in the map must be a real registered tool.
    assert set(mapping.values()) == set(MCP_TOOL_NAMES)
    assert len(mapping) == 8
    # Canonical Actions op names expected on the left side.
    assert set(mapping.keys()) == {
        "gpt_get_catalog",
        "gpt_list_playlists",
        "gpt_get_playlist_context",
        "gpt_search_data_routes",
        "gpt_inspect_data_model",
        "gpt_preview_data_model",
        "gpt_preview_change",
        "gpt_commit_change",
    }
    # Actions-only auxiliaries are explicit non-parity.
    for op in parity["not_exposed_in_mcp"]:
        assert op not in MCP_TOOL_NAMES


def test_write_flow_mcp_semantics():
    intel = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    wf = intel["write_flow_mcp"]
    assert wf["principle"] == "GOVERNED_ENVELOPE_PREPARE_THEN_ACT"
    additive = wf["additive"]
    assert "prepare_change" in additive and "commit_proposal" in additive
    assert "confirmation=true" in additive and "idempotency_key" in additive
    assert "commit_now" not in additive  # MCP has no commit_now
    destructive = wf["destructive"]
    assert "prepare_change" in destructive and "Confirma?" in destructive
    # Idempotency discipline: same logical attempt = same key; new mutation = new key.
    assert "MESMA key" in wf["idempotency_key"] or "mesma key" in wf["idempotency_key"].lower()
    # Unknown outcome: reconcile before retry, never cross-transport replay.
    assert "UNKNOWN_OUTCOME" in wf["unknown_outcome"]
    assert "nunca" in wf["unknown_outcome"].lower()
    assert "NUNCA" in wf["no_cross_transport_act_replay"]
    assert "GPT Actions" in wf["no_cross_transport_act_replay"]
    # Error is not empty data.
    assert "data_model.not_found" in wf["error_is_not_empty"]
    assert "OUTCOME_NOT_VERIFIED" in wf["error_is_not_empty"]
    # Success requires verified postcondition.
    assert "VERIFIED" in wf["success_requires"]


def test_write_flow_actions_variant_preserved():
    """Coexistence: the Actions write_flow remains for the Actions transport."""
    intel = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    assert "write_flow" in intel
    assert "gpt_preview_change" in intel["write_flow"]["additive"]
    assert "gpt_commit_change" in intel["write_flow"]["destructive"]


# ---------------------------------------------------------------------------
# Builder instructions — MCP variant
# ---------------------------------------------------------------------------


def test_mcp_instructions_fit_budget():
    block = _mcp_instructions_block()
    assert len(block) <= PROJECT_TARGET_LIMIT, len(block)


def test_mcp_instructions_required_markers():
    block = _mcp_instructions_block()
    required = [
        "VISTA — Especialista em Painéis Operacionais DELPI",
        "INFERRED != FACT",
        "PROPOSED != SAVED",
        "PREVIEW != PERSISTED",
        "TECHNICAL SUCCESS != VERIFIED BUSINESS OUTCOME",
        "Search miss != proof of absence",
        "VISTA capability <= capability do usuário autenticado",
        "confirmation != authorization",
        "2xx != verified",
        "401=AuthN",
        "403=AuthZ",
        "proposal_handle",
        "latest",
        "get_catalog",
        "agent_directives",
        "prepare_change",
        "commit_proposal",
        "idempotency_key",
        "confirmation=true",
        "VERIFIED",
        "UNKNOWN_OUTCOME",
    ]
    for marker in required:
        assert marker in block, marker


def test_mcp_instructions_no_actions_or_leaks():
    block = _mcp_instructions_block()
    # No GPT Actions op names inside the MCP variant.
    for gpt_op in (
        "gpt_get_catalog",
        "gpt_preview_change",
        "gpt_commit_change",
        "commit_now",
    ):
        assert gpt_op not in block, gpt_op
    # No mutable directive section names leaked into stable instructions.
    for section in (
        "object_resolution",
        "screenshot_parity",
        "layout_perception",
        "filter_layering",
        "slide_craft",
        "continuous_review",
        "execution_posture",
        "anti_patterns",
        "ALTER_EXISTING_BEFORE_CREATE",
        "EXECUTE_TYPED_CHANGE_NOW",
    ):
        assert section not in block, section


def test_actions_instructions_variant_preserved():
    block = _actions_instructions_block()
    assert "gpt_preview_change" in block
    assert "gpt_commit_change" in block
    assert "commit_now=true" in block


# ---------------------------------------------------------------------------
# Intelligence surface still served through get_catalog (same for MCP clients)
# ---------------------------------------------------------------------------


def test_mcp_sections_documented_but_not_projected():
    """MCP3 parity/write sections are canonical in the JSON document but are
    intentionally NOT projected into agent_directives: the Actions catalog
    envelope is already at its byte ceiling (known headroom backlog). The MCP
    instructions variant carries the envelope skeleton inline instead."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    intel = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    assert "write_flow_mcp" in intel
    assert "surface_parity" in intel

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    assert "write_flow_mcp" not in directives
    assert "surface_parity" not in directives
    clear_vista_agent_intelligence_cache()
