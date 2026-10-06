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


def test_mcp_surface_exactly_ten_with_analysis():
    tools = asyncio.run(create_mcp_server().list_tools())
    assert {t.name for t in tools} == set(MCP_TOOL_NAMES)
    assert len(tools) == 10
    assert TOOL_CLASS["prepare_change"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"
    assert TOOL_CLASS["preview_data_block"] == "ANALYSIS"
    assert TOOL_CLASS["suggest_change"] == "ANALYSIS"


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
    assert len(mapping) == 10
    # Canonical Actions op names expected on the left side.
    assert set(mapping.keys()) == {
        "gpt_get_catalog",
        "gpt_list_playlists",
        "gpt_get_playlist_context",
        "gpt_search_data_routes",
        "gpt_inspect_data_model",
        "gpt_preview_data_model",
        "gpt_preview_data_block",
        "gpt_suggest_change",
        "gpt_preview_change",
        "gpt_commit_change",
    }
    # Actions-only auxiliaries are explicit non-parity (signed artifact route).
    for op in parity["not_exposed_in_mcp"]:
        assert op not in MCP_TOOL_NAMES
    assert parity["not_exposed_in_mcp"] == ["gpt_get_slide_preview_png"]


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


def test_mcp_sections_projected_into_agent_directives():
    """MCP3 parity/write sections are canonical in the JSON document AND
    projected into agent_directives: the shared directives are now
    transport-neutral, so both transports get the same live surface."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    intel = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    assert "write_flow_mcp" in intel
    assert "surface_parity" in intel

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    assert "write_flow_mcp" in directives
    assert "surface_parity" in directives
    # Parity map survives compaction intact: 10 Actions↔MCP mappings cover the
    # registered tool set (analysis surface included, §6.133 + suggest_change).
    parity = directives["surface_parity"]
    mapping = parity["parity_map"]
    assert len(mapping) == 10
    assert set(mapping.values()) == set(MCP_TOOL_NAMES)
    clear_vista_agent_intelligence_cache()


def test_agent_directives_mcp_primary_tool_names():
    """Live directives must name the real MCP tools in primary guidance."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    blob = json.dumps(directives, ensure_ascii=False)
    for tool in (
        "get_catalog",
        "get_playlist_context",
        "list_playlists",
        "search_data_routes",
        "inspect_data_model",
        "preview_data_model",
        "suggest_change",
        "prepare_change",
        "commit_proposal",
    ):
        assert tool in blob, tool
    clear_vista_agent_intelligence_cache()


def _stale_gpt_refs(node, path=()):
    """Collect gpt_* mentions outside labeled Actions-compatibility zones."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            found += _stale_gpt_refs(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found += _stale_gpt_refs(v, path + (str(i),))
    elif isinstance(node, str) and "gpt_" in node:
        found.append((".".join(path), node))
    return found


def test_agent_directives_no_unlabeled_actions_names():
    """gpt_* names may only appear inside the labeled Actions write_flow
    variant, the parity map, or prose explicitly tagged '(Actions: ...)'."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    refs = _stale_gpt_refs(directives)
    for path, text in refs:
        if path.startswith("surface_parity"):
            continue  # the parity map is the compatibility registry itself
        if path.startswith("write_flow."):
            # whole section is the labeled Actions variant
            assert directives["write_flow"]["surface"] == "gpt_actions"
            continue
        assert "Actions" in text, f"unlabeled gpt_* reference at {path}: {text}"
    clear_vista_agent_intelligence_cache()


def test_write_flow_actions_variant_labeled():
    """The legacy write_flow keeps Actions semantics but must be labeled so
    MCP-facing readers don't treat commit_now/confirmation.confirmed as the
    primary execution path."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    # Canonical document keeps the Actions label; the MCP projection strips
    # Actions-envelope labeling — surface/note/additive/destructive name
    # gpt_* mechanics that are not MCP-callable semantics.
    canonical = VistaAgentIntelligenceService.document()["write_flow"]
    assert canonical["surface"] == "gpt_actions"
    assert "write_flow_mcp" in canonical["note"]
    write_flow = VistaAgentIntelligenceService.agent_directives()["write_flow"]
    for actions_key in ("surface", "note", "additive", "destructive"):
        assert actions_key not in write_flow
    for neutral_key in ("compound", "same_turn", "refuse_only_when", "forbidden_handles"):
        assert neutral_key in write_flow
    clear_vista_agent_intelligence_cache()


def test_write_flow_mcp_projected_confirmation_semantics():
    """MCP-facing write flow: PREPARE != ACT, opaque handle, explicit
    confirmation, stable idempotency, no cross-transport ACT replay."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    wf = directives["write_flow_mcp"]
    assert "prepare_change" in wf["additive"]
    assert "commit_proposal" in wf["additive"]
    assert "confirmation=true" in wf["additive"]
    assert "commit_now" not in json.dumps(wf, ensure_ascii=False)
    assert "confirmation.confirmed" not in json.dumps(wf, ensure_ascii=False)
    assert "mesma key" in wf["idempotency_key"].lower()
    assert "read-back" in wf["unknown_outcome"].lower()
    assert "persisted=true" in wf["success_requires"]
    clear_vista_agent_intelligence_cache()


def test_mcp_delia_status_scoped_to_delia_adapter():
    """VISTA MCP is LIVE; TARGET refers only to the future DÉLIA adapter."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    mcp_delia = directives["mcp_delia"]
    assert mcp_delia["vista_mcp"] == "LIVE"
    assert mcp_delia["status"] == "TARGET"
    assert mcp_delia["status_scope"] == "delia_adapter"
    assert mcp_delia["primary_transport"] == "MCP"
    clear_vista_agent_intelligence_cache()


def test_actions_transport_directives_drop_mcp_sections():
    """The Actions catalog variant stays inside the OpenAI byte ceiling:
    MCP-facing sections are projected only for transport="mcp"."""
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
        clear_vista_agent_intelligence_cache,
    )

    clear_vista_agent_intelligence_cache()
    actions = VistaAgentIntelligenceService.agent_directives(transport="actions")
    assert "surface_parity" not in actions
    assert "write_flow_mcp" not in actions
    assert "mcp_delia" not in actions
    assert "write_flow" in actions  # Actions variant keeps its own write flow
    assert "surface" not in actions["write_flow"]
    mcp = VistaAgentIntelligenceService.agent_directives(transport="mcp")
    assert "surface_parity" in mcp
    assert "write_flow_mcp" in mcp
    clear_vista_agent_intelligence_cache()
