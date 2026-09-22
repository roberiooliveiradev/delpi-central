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
# Capability parity: GPT operationId → MCP tool names (1→N allowed)
# ---------------------------------------------------------------------------

GPT_TO_MCP_TOOLS: dict[str, tuple[str, ...]] = {
    "gpt_get_my_context": ("get_my_context",),
    "gpt_get_catalog": ("get_catalog",),
    "gpt_get_methodology_guide": ("get_methodology_guide",),
    "gpt_get_process_context": ("get_process_context",),
    "gpt_analyze": ("analyze",),
    "gpt_search_records": ("search_records",),
    "gpt_get_record": ("get_record",),
    "gpt_prepare_record_change": ("prepare_record_change",),
    "gpt_commit_proposal": ("commit_proposal",),
    "gpt_activate_revision": ("prepare_activate_revision",),
    "gpt_recalculate_dashboard": ("prepare_recalculate_dashboard",),
    "gpt_meeting_minute_workflow": ("prepare_meeting_minute_workflow",),
    "gpt_validate_improvement_package": ("prepare_improvement_package",),
    "gpt_list_evidence": ("list_evidence",),
    "gpt_manage_evidence": ("prepare_manage_evidence",),
    "gpt_get_process_timeline": ("get_process_timeline",),
    "gpt_adjust_shared_resource_cost": ("prepare_adjust_shared_resource_cost",),
    "gpt_meeting_minute_manage": (
        "meeting_minute_read",
        "generate_from_transcript",
        "prepare_meeting_minute_manage",
    ),
}

TOOL_TO_GPT_OPERATION: dict[str, str] = {
    tool: gpt_op
    for gpt_op, tools in GPT_TO_MCP_TOOLS.items()
    for tool in tools
}

# MCP tools with no GPT Action. Methodology is on both surfaces.
MCP_NATIVE_TOOLS: frozenset[str] = frozenset()

# READ | PREPARE | ACT | ANALYSIS (non-persist)
# ACT class retained for commit_proposal (common governed commit).
TOOL_CLASS: dict[str, str] = {
    "get_my_context": "READ",
    "get_catalog": "READ",
    "get_methodology_guide": "READ",
    "get_process_context": "READ",
    "analyze": "READ",
    "search_records": "READ",
    "get_record": "READ",
    "list_evidence": "READ",
    "get_process_timeline": "READ",
    "meeting_minute_read": "READ",
    "generate_from_transcript": "ANALYSIS",
    "prepare_record_change": "PREPARE",
    "prepare_activate_revision": "PREPARE",
    "prepare_recalculate_dashboard": "PREPARE",
    "prepare_meeting_minute_workflow": "PREPARE",
    "prepare_improvement_package": "PREPARE",
    "prepare_manage_evidence": "PREPARE",
    "prepare_adjust_shared_resource_cost": "PREPARE",
    "prepare_meeting_minute_manage": "PREPARE",
    "commit_proposal": "ACT",
}

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
    }
)

# Kept for internal bridge compatibility / residual checks (capability keys).
ACT_TOOL_CAPABILITY: dict[str, str] = {
    "commit_proposal": "",  # capability derived from stored proposal
}

PREPARE_TOOL_CAPABILITY: dict[str, str] = {
    "prepare_record_change": "create_record",  # operation selects exact capability
    "prepare_activate_revision": "activate_revision",
    "prepare_recalculate_dashboard": "recalculate_dashboard",
    "prepare_meeting_minute_workflow": "meeting_minute_workflow",
    "prepare_improvement_package": "commit_improvement_package",
    "prepare_manage_evidence": "manage_evidence",
    "prepare_adjust_shared_resource_cost": "adjust_shared_resource_cost",
    "prepare_meeting_minute_manage": "meeting_minute_manage",
}
