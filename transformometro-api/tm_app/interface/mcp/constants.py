"""Frozen TÉO MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. Do not rename for «TÉO».

Write surface (V2): PREPARE → opaque proposal_handle → commit_proposal.
Entity CRUD uses prepare_record_change; specialized workflows keep explicit PREPARE.
GPT Actions V2 shares the same GovernedWriteOrchestrator / GovernedActionsFacade.
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP (not chatgpt-transformometro).
MCP_PREDEFINED_CLIENT_ID = "mcp-transformometro"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/transformometro-api/mcp"

MCP_GATEWAY_ROOT = "/apps/transformometro-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# GPT Actions Builder surface is prepare/commit governed (legacy CRUD shims remain off-OpenAPI).
GPT_ACTIONS_LIFECYCLE = "GOVERNED_PREPARE_COMMIT_V2"

# MCP Plugin surface: capability-driven (generic entity + common commit + specialized PREPARE).
TEO_MCP_SURFACE = "CAPABILITY_GOVERNED_V2"

# ---------------------------------------------------------------------------
# Capability parity — DERIVED from the canonical inward registry
# (tm_app.application.intelligence.capability_registry). Adapters consume
# the model; the model never imports this module.
# ---------------------------------------------------------------------------

from tm_app.application.intelligence.capability_registry import (
    actions_parity,
    mcp_native_tool_names,
    mcp_tool_classes,
    mcp_tool_to_actions,
)

# Capability parity: GPT operationId → MCP tool names (1→N allowed)
GPT_TO_MCP_TOOLS: dict[str, tuple[str, ...]] = actions_parity()

TOOL_TO_GPT_OPERATION: dict[str, str] = mcp_tool_to_actions()

# MCP tools with no GPT Action. Diagnostic V1 is MCP-native in this slice —
# GPT parity, if desired, is a separate decision (no fake parity mapping).
MCP_NATIVE_TOOLS: frozenset[str] = mcp_native_tool_names()

# READ | PREPARE | ACT | ANALYSIS (non-persist)
# ACT class retained for commit_proposal (common governed commit).
TOOL_CLASS: dict[str, str] = mcp_tool_classes()

# commit_proposal may execute destructive capabilities → truthful annotation.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset({"commit_proposal"})

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

MCP_SURFACE_BUDGET = {
    "before_total": 33,
    "before": {"READ": 10, "ANALYSIS": 1, "PREPARE": 11, "ACT": 11},
    "after_total": len(MCP_TOOL_NAMES),
    "after": {
        "READ": sum(1 for v in TOOL_CLASS.values() if v == "READ"),
        "ANALYSIS": sum(1 for v in TOOL_CLASS.values() if v == "ANALYSIS"),
        "PREPARE": sum(1 for v in TOOL_CLASS.values() if v == "PREPARE"),
        "ACT": sum(1 for v in TOOL_CLASS.values() if v == "ACT"),
    },
    "principle": (
        "Eliminate mechanical CRUD PREPARE/ACT pairs; keep specialized business PREPARE; "
        "common commit_proposal; new CRUD entity ⇒ 0 new MCP tools."
    ),
}

# Legacy tool names removed from registration (V1 mechanical pairs).
# Bridge wrappers may still exist for unit tests; not discoverable via list_tools.
MCP_LEGACY_REMOVED_TOOLS: frozenset[str] = frozenset(
    {
        "prepare_create_record",
        "prepare_update_record",
        "prepare_delete_record",
        "prepare_duplicate_record",
        "act_create_record",
        "act_update_record",
        "act_delete_record",
        "act_duplicate_record",
        "act_activate_revision",
        "act_recalculate_dashboard",
        "act_meeting_minute_workflow",
        "act_commit_improvement_package",
        "act_manage_evidence",
        "act_adjust_shared_resource_cost",
        "act_meeting_minute_manage",
        # Tool Surface Rationalization V1 — pre-family tool names.
        # Capabilities are unchanged; old names are tombstones that fail
        # closed. Canonical replacements:
        #   task_read / interaction_room_read   → collaboration_read
        #   prepare_task / prepare_interaction_room → prepare_collaboration_change
        #   list_evidence → evidence_read; prepare_manage_evidence → prepare_evidence_change
        #   generate_from_transcript → meeting_minute_read(action)
        #   prepare_meeting_minute_workflow / prepare_meeting_minute_manage
        #       → prepare_meeting_minute_change
        #   get_diagnostic / list_diagnostics_by_revision → diagnostic_read
        #   prepare_create_diagnostic / prepare_manage_diagnostic
        #       → prepare_diagnostic_change
        #   prepare_activate_revision / prepare_recalculate_dashboard /
        #   prepare_improvement_package / prepare_adjust_shared_resource_cost
        #       → prepare_governed_operation
        "task_read",
        "prepare_task",
        "interaction_room_read",
        "prepare_interaction_room",
        "list_evidence",
        "prepare_manage_evidence",
        "generate_from_transcript",
        "prepare_meeting_minute_workflow",
        "prepare_meeting_minute_manage",
        "get_diagnostic",
        "list_diagnostics_by_revision",
        "prepare_create_diagnostic",
        "prepare_manage_diagnostic",
        "prepare_activate_revision",
        "prepare_recalculate_dashboard",
        "prepare_improvement_package",
        "prepare_adjust_shared_resource_cost",
    }
)

# Kept for internal bridge compatibility / residual checks (capability keys).
ACT_TOOL_CAPABILITY: dict[str, str] = {
    "commit_proposal": "",  # capability derived from stored proposal
}

PREPARE_TOOL_CAPABILITY: dict[str, str] = {
    # Multi-action families: the ``action`` argument selects the exact
    # semantic capability (and therefore its canonical execution_policy);
    # the value shown is only the representative/default capability.
    "prepare_record_change": "create_record",  # operation selects exact capability
    "prepare_collaboration_change": "create_task",  # action selects exact capability
    "prepare_evidence_change": "manage_evidence",  # action selects operation
    "prepare_meeting_minute_change": "meeting_minute_manage",  # action selects
    "prepare_diagnostic_change": "manage_diagnostic",  # action selects
    "prepare_governed_operation": "activate_revision",  # action selects
}
