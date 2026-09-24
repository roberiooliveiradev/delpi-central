"""TÉO agent_directives + confirmation policy + commit_now hygiene."""

from __future__ import annotations

import pytest

from tm_app.application.governed_writes.confirmation_policy import (
    allows_commit_now_for_capability,
    allows_commit_now_for_entity_operation,
    allows_commit_now_for_workflow,
)
from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
    clear_teo_agent_intelligence_cache,
)
from tm_app.interface.mcp.branding import TEO_MCP_INSTRUCTIONS


def setup_function() -> None:
    clear_teo_agent_intelligence_cache()


def teardown_function() -> None:
    clear_teo_agent_intelligence_cache()


def test_teo_agent_intelligence_loads_version():
    assert TeoAgentIntelligenceService.version()
    doc = TeoAgentIntelligenceService.document()
    assert doc.get("owner") == "transformometro-api"
    assert "flows" in doc
    assert "meeting_minutes" in doc["flows"]


def test_capability_surface_projects_agent_directives():
    surface = build_capability_surface_catalog()
    assert surface["rules"]["agent_directives_are_live"] is True
    directives = surface["agent_directives"]
    assert directives["version"] == TeoAgentIntelligenceService.version()
    assert "write_flow" in directives
    assert "commit_now" in str(directives["write_flow"]).lower()
    assert "meeting_minute" in str(directives["discovery"]).lower()
    assert "TRY_ACTION_BEFORE_CLAIMING_UNAVAILABLE" in str(
        directives["actions_runtime"]
    )


def test_confirmation_policy_pos_sib_neg():
    assert allows_commit_now_for_entity_operation("create")
    assert allows_commit_now_for_entity_operation("update")
    assert allows_commit_now_for_entity_operation("duplicate")
    assert not allows_commit_now_for_entity_operation("delete")
    assert allows_commit_now_for_capability("commit_improvement_package")
    assert allows_commit_now_for_capability("adjust_shared_resource_cost")
    assert not allows_commit_now_for_capability("activate_revision")
    assert not allows_commit_now_for_workflow("meeting_minute_workflow")
    assert allows_commit_now_for_workflow("improvement_package")


def test_entity_confirmation_policy_labels_on_catalog():
    surface = build_capability_surface_catalog()
    process = next(e for e in surface["entities"] if e["id"] == "process")
    assert process["confirmation_policy"]["create"] == "commit_now_allowed_additive"
    assert process["confirmation_policy"]["delete"] == (
        "explicit_user_confirmation_before_commit"
    )
    pkg = next(w for w in surface["workflows"] if w["id"] == "improvement_package")
    assert pkg["confirmation_policy"] == "commit_now_allowed_additive"
    act = next(w for w in surface["workflows"] if w["id"] == "activate_revision")
    assert act["confirmation_policy"] == "explicit_user_confirmation_before_commit"


def test_mcp_branding_obeys_directives_not_universal_package_confirm():
    text = TEO_MCP_INSTRUCTIONS
    assert "agent_directives" in text
    assert "commit_now" in text
    assert "sempre confirmation antes de package" not in text.lower()
    assert "do not ask Confirma?" in text or "Confirma?" in text


def test_intelligence_json_covers_all_gpt_ops_and_mcp_tools():
    from tm_app.application.gpt_actions.openapi_builder import GPT_ACTIONS_OPERATION_IDS
    from tm_app.interface.mcp.constants import MCP_TOOL_NAMES

    doc = TeoAgentIntelligenceService.document()
    flows = doc.get("flows") or {}
    gpt_seen: set[str] = set()
    mcp_seen: set[str] = set()
    for flow in flows.values():
        if not isinstance(flow, dict):
            continue
        gpt_seen.update(flow.get("gpt_operations") or [])
        mcp_seen.update(flow.get("mcp_tools") or [])
    # All current importable GPT ops referenced at least once
    missing_gpt = sorted(set(GPT_ACTIONS_OPERATION_IDS) - gpt_seen)
    assert not missing_gpt, missing_gpt
    missing_mcp = sorted(set(MCP_TOOL_NAMES) - mcp_seen)
    assert not missing_mcp, missing_mcp


def test_facade_and_mcp_share_orchestrator_class():
    from tm_app.application.gpt_actions.governed_actions_facade import (
        GovernedActionsFacade,
    )
    from tm_app.application.governed_writes.orchestrator import (
        GovernedWriteOrchestrator,
    )
    from tm_app.interface.mcp import tool_bridge

    facade = GovernedActionsFacade()
    assert isinstance(facade.orchestrator, GovernedWriteOrchestrator)
    assert tool_bridge._governed.orchestrator.__class__ is GovernedWriteOrchestrator
