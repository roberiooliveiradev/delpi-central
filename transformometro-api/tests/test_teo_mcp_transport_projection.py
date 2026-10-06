"""TÉO unified capability/intelligence boundary — transport projections.

The same canonical intelligence (teo_agent_intelligence.json + capability
descriptors + registration guide) feeds both transports. The Actions
projection keeps ``gpt_*`` names and the additive ``commit_now`` policy;
the MCP projection must expose only MCP-callable names and the pure
PREPARE → commit_proposal contract — zero ``commit_now``, zero ``gpt_*``.
"""

from __future__ import annotations

import json

import pytest

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.registration_guide import (
    build_registration_guide,
)
from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
    clear_teo_agent_intelligence_cache,
)
from tm_app.application.intelligence.transport_projection import (
    actions_to_mcp_primary,
)
from tm_app.interface.mcp.constants import GPT_TO_MCP_TOOLS, MCP_TOOL_NAMES


def setup_function() -> None:
    clear_teo_agent_intelligence_cache()


def teardown_function() -> None:
    clear_teo_agent_intelligence_cache()


def _blob(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


# --- MCP projection: zero Actions semantics ---------------------------------


def test_mcp_agent_directives_no_actions_semantics():
    directives = TeoAgentIntelligenceService.agent_directives(transport="mcp")
    blob = _blob(directives)
    assert "gpt_" not in blob
    assert "commit_now" not in blob
    assert "write_flow" not in directives
    assert directives["write_flow_mcp"]
    for flow in (directives.get("flows") or {}).values():
        assert "gpt_operations" not in flow
    parity = directives.get("surface_parity") or {}
    assert "parity_map" not in parity
    assert "gpt_actions" not in json.dumps(parity)


def test_mcp_capability_surface_callable_names_only():
    surface = build_capability_surface_catalog(projection="mcp")
    blob = _blob(surface)
    assert "gpt_" not in blob
    assert "commit_now" not in blob
    assert surface["surface_version"] != "teo-gpt-actions-v2"
    assert surface["proposal_model"]["commit_operation"] == "commit_proposal"
    assert "commit_now_parameter" not in surface["proposal_model"]
    names = set(MCP_TOOL_NAMES)
    for workflow in surface["workflows"]:
        assert workflow["prepare_operation"] in names
        assert workflow["commit_via"] in names
    for analysis in surface["analyses"]:
        assert analysis["operation"] in names
    for entity in surface["entities"]:
        if entity.get("write_operations"):
            assert "commit_now" not in entity["prepare_act_policy"]


def test_mcp_registration_guide_callable_names_only():
    guide = build_registration_guide(transport="mcp")
    blob = _blob(guide)
    assert "gpt_" not in blob
    assert "commit_now" not in blob
    assert "legacy_removed_from_builder" not in blob
    assert "prepare_record_change" in blob
    assert "commit_proposal" in blob


def test_mcp_directives_flows_mcp_names_callable():
    directives = TeoAgentIntelligenceService.agent_directives(transport="mcp")
    names = set(MCP_TOOL_NAMES)
    for flow_id, flow in (directives.get("flows") or {}).items():
        for tool in flow.get("mcp_tools") or []:
            assert tool in names, f"{flow_id} lists non-callable MCP tool {tool}"


# --- Actions projection: contract preserved ---------------------------------


def test_actions_agent_directives_preserve_actions_contract():
    directives = TeoAgentIntelligenceService.agent_directives()
    assert "commit_now" in _blob(directives["write_flow"]).lower()
    assert "write_flow_mcp" not in directives
    posture = directives["execution_posture"]
    assert any("commit_now" in rule for rule in posture["rules"])
    assert any("commit_now" in item for item in posture["forbidden"])
    assert any("commit_now" in item for item in directives["anti_patterns"])
    parity = directives.get("surface_parity") or {}
    assert parity["parity_map"]["gpt_commit_proposal"] == ["commit_proposal"]
    assert parity["parity_map_primary"]["gpt_get_catalog"] == "get_catalog"


def test_actions_capability_surface_unchanged():
    surface = build_capability_surface_catalog()
    assert surface["surface_version"] == "teo-gpt-actions-v2"
    assert surface["proposal_model"]["commit_now_parameter"] is True
    assert surface["proposal_model"]["commit_operation"] == "gpt_commit_proposal"
    workflow = surface["workflows"][0]
    assert workflow["prepare_operation"].startswith("gpt_")
    assert workflow["commit_via"] == "gpt_commit_proposal"


def test_actions_registration_guide_unchanged():
    guide = build_registration_guide()
    blob = _blob(guide)
    assert "gpt_prepare_record_change" in blob
    assert "gpt_commit_proposal" in blob
    assert "legacy_removed_from_builder" in _blob(
        guide.get("write_contract_rules") or {}
    )


# --- Parity map: single canonical record ------------------------------------


def test_parity_map_derives_from_canonical_record():
    mapping = actions_to_mcp_primary()
    assert set(mapping.keys()) == set(GPT_TO_MCP_TOOLS.keys())
    names = set(MCP_TOOL_NAMES)
    assert set(mapping.values()) <= names
    assert mapping["gpt_commit_proposal"] == "commit_proposal"
    assert mapping["gpt_prepare_record_change"] == "prepare_record_change"
    # 1→N parity picks the write-path tool as primary.
    assert mapping["gpt_meeting_minute_manage"] == "prepare_meeting_minute_manage"
