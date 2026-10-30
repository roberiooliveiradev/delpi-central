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

# MCP Plugin surface: Semantic V3 ONLY (issue #124 — final cutover).
# The six semantic tools are the entire public surface; the 23 V2 family
# names are tombstoned (their bridge functions remain internal adapters
# consumed by tool_bridge_v3 — capability/AuthZ/policy resolution is
# unchanged). GPT Actions keep their own gpt_* contract.
TEO_MCP_SURFACE = "SEMANTIC_V3_ONLY"

# ---------------------------------------------------------------------------
# Capability parity — DERIVED from the canonical inward registry
# (tm_app.application.intelligence.capability_registry). Adapters consume
# the model; the model never imports this module.
# ---------------------------------------------------------------------------

from tm_app.application.intelligence.capability_registry import (
    actions_to_v3_parity,
    mcp_tool_to_actions,
)

# Semantic V3 surface (issue #124 — final cutover): the ONLY six public
# tools. Classes follow the shared delpi_mcp taxonomy; execute/delete are
# ACT (they may persist state).
V3_TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
    "execute": "ACT",
    "delete": "ACT",
}
V3_SEMANTIC_TOOL_NAMES: frozenset[str] = frozenset(V3_TOOL_CLASS)

# Capability parity: GPT operationId → Semantic V3 tool names (1→N).
# Derived from the canonical registry — an Actions op maps to the V3
# tool(s) serving its bound capability route.
GPT_TO_MCP_TOOLS: dict[str, tuple[str, ...]] = actions_to_v3_parity()

# Semantic V3 tool → Actions operationIds it serves (inverse parity).
V3_TOOL_TO_GPT_OPS: dict[str, tuple[str, ...]] = {
    tool: tuple(
        op for op, tools in GPT_TO_MCP_TOOLS.items() if tool in tools
    )
    for tool in V3_SEMANTIC_TOOL_NAMES
}

# Legacy-name → owning Actions operationId — kept for tombstone audits
# and internal compatibility only; not a discoverable surface map.
TOOL_TO_GPT_OPERATION: dict[str, str] = mcp_tool_to_actions()

# MCP tools with no direct GPT Action name. The semantic names are
# transport-level adapters — only ``analyze`` coincides with a registered
# GPT operation binding.
MCP_NATIVE_TOOLS: frozenset[str] = V3_SEMANTIC_TOOL_NAMES - {"analyze"}

# READ | PREPARE | ACT | ANALYSIS (non-persist) | DISCOVERY
TOOL_CLASS: dict[str, str] = dict(V3_TOOL_CLASS)

# Destructive-capable public tools — truthful annotation.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset({"delete"})

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
        "Semantic V3 ONLY: six semantic tools over the governed "
        "capability surface — entity/action vocabulary rides inside "
        "typed arguments; new capabilities ⇒ 0 new MCP tools."
    ),
}

# Semantic V3 final cutover (issue #124) — the 22 V2 family names removed
# from public registration (``analyze`` survives as a V3 tool). All
# capabilities are unchanged; each route is served by a semantic tool
# (capability_registry.MCP_TO_V3_TOOL is the canonical route map).
# Bridge functions remain internal adapters.
MCP_V2_REMOVED_TOOLS: frozenset[str] = frozenset(
    {
        "get_my_context",
        "get_workspace_context",
        "get_catalog",
        "get_methodology_guide",
        "get_product_guide",
        "solution_read",
        "get_process_context",
        "get_process_timeline",
        "record_read",
        "helpdesk_read",
        "meeting_minute_read",
        "evidence_read",
        "collaboration_read",
        "diagnostic_read",
        "prepare_record_change",
        "prepare_governed_operation",
        "prepare_helpdesk_change",
        "prepare_meeting_minute_change",
        "prepare_evidence_change",
        "prepare_collaboration_change",
        "prepare_diagnostic_change",
        "commit_proposal",
    }
)
# ``analyze`` is NOT tombstoned — it is a V3 semantic tool.

# Legacy tool names removed from registration (V1 mechanical pairs +
# pre-family consolidation wave). The V2 family names they referenced as
# replacements are themselves tombstoned by the Semantic V3 cutover —
# routes now live in capability_registry.MCP_TO_V3_TOOL. Bridge wrappers
# may still exist for internal adapters/unit tests; nothing here is
# discoverable via list_tools.
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
        # Knowledge Orchestration V1 — read-family consolidation:
        #   get_solution_catalog / get_solution_context → solution_read
        #   search_records / get_record → record_read
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
        "get_solution_catalog",
        "get_solution_context",
        "search_records",
        "get_record",
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
    "prepare_helpdesk_change": "helpdesk_create_ticket",  # action selects
}
