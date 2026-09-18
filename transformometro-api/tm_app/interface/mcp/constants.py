"""Frozen TÉO MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. Do not rename for «TÉO».

Write surface uses PREPARE → proposal_handle → ACT (governed writes).
GPT Actions HTTP façade remains LEGACY_TRANSITIONAL_BRIDGE without proposal handles.
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP (not chatgpt-transformometro).
MCP_PREDEFINED_CLIENT_ID = "mcp-transformometro"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/transformometro-api/mcp"

MCP_GATEWAY_ROOT = "/apps/transformometro-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# GPT Actions bridge remains available; MCP is the Plugin/Agent target.
GPT_ACTIONS_LIFECYCLE = "LEGACY_TRANSITIONAL_BRIDGE"

TEO_MCP_SURFACE = "FULL_CRUD_GOVERNED"

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
    "gpt_create_record": ("prepare_create_record", "act_create_record"),
    "gpt_update_record": ("prepare_update_record", "act_update_record"),
    "gpt_delete_record": ("prepare_delete_record", "act_delete_record"),
    "gpt_duplicate_record": ("prepare_duplicate_record", "act_duplicate_record"),
    "gpt_activate_revision": ("prepare_activate_revision", "act_activate_revision"),
    "gpt_recalculate_dashboard": (
        "prepare_recalculate_dashboard",
        "act_recalculate_dashboard",
    ),
    "gpt_meeting_minute_workflow": (
        "prepare_meeting_minute_workflow",
        "act_meeting_minute_workflow",
    ),
    "gpt_validate_improvement_package": ("prepare_improvement_package",),
    "gpt_commit_improvement_package": ("act_commit_improvement_package",),
    "gpt_list_evidence": ("list_evidence",),
    "gpt_manage_evidence": ("prepare_manage_evidence", "act_manage_evidence"),
    "gpt_get_process_timeline": ("get_process_timeline",),
    "gpt_adjust_shared_resource_cost": (
        "prepare_adjust_shared_resource_cost",
        "act_adjust_shared_resource_cost",
    ),
    "gpt_meeting_minute_manage": (
        "meeting_minute_read",
        "generate_from_transcript",
        "prepare_meeting_minute_manage",
        "act_meeting_minute_manage",
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
    "prepare_create_record": "PREPARE",
    "prepare_update_record": "PREPARE",
    "prepare_delete_record": "PREPARE",
    "prepare_duplicate_record": "PREPARE",
    "prepare_activate_revision": "PREPARE",
    "prepare_recalculate_dashboard": "PREPARE",
    "prepare_meeting_minute_workflow": "PREPARE",
    "prepare_improvement_package": "PREPARE",
    "prepare_manage_evidence": "PREPARE",
    "prepare_adjust_shared_resource_cost": "PREPARE",
    "prepare_meeting_minute_manage": "PREPARE",
    "act_create_record": "ACT",
    "act_update_record": "ACT",
    "act_delete_record": "ACT",
    "act_duplicate_record": "ACT",
    "act_activate_revision": "ACT",
    "act_recalculate_dashboard": "ACT",
    "act_meeting_minute_workflow": "ACT",
    "act_commit_improvement_package": "ACT",
    "act_manage_evidence": "ACT",
    "act_adjust_shared_resource_cost": "ACT",
    "act_meeting_minute_manage": "ACT",
}

# Destructive / overwriting ACTs — annotations must be truthful.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset(
    {
        "act_delete_record",
        "act_manage_evidence",  # delete op
        "act_activate_revision",  # overwrites current
        "act_meeting_minute_workflow",  # cancel/finalize consequential
        "act_meeting_minute_manage",  # resend/overwrite-ish
        "act_commit_improvement_package",  # multi-write
    }
)

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# ACT tool name → governed capability key
ACT_TOOL_CAPABILITY: dict[str, str] = {
    "act_create_record": "create_record",
    "act_update_record": "update_record",
    "act_delete_record": "delete_record",
    "act_duplicate_record": "duplicate_record",
    "act_activate_revision": "activate_revision",
    "act_recalculate_dashboard": "recalculate_dashboard",
    "act_meeting_minute_workflow": "meeting_minute_workflow",
    "act_commit_improvement_package": "commit_improvement_package",
    "act_manage_evidence": "manage_evidence",
    "act_adjust_shared_resource_cost": "adjust_shared_resource_cost",
    "act_meeting_minute_manage": "meeting_minute_manage",
}

PREPARE_TOOL_CAPABILITY: dict[str, str] = {
    "prepare_create_record": "create_record",
    "prepare_update_record": "update_record",
    "prepare_delete_record": "delete_record",
    "prepare_duplicate_record": "duplicate_record",
    "prepare_activate_revision": "activate_revision",
    "prepare_recalculate_dashboard": "recalculate_dashboard",
    "prepare_meeting_minute_workflow": "meeting_minute_workflow",
    "prepare_improvement_package": "commit_improvement_package",
    "prepare_manage_evidence": "manage_evidence",
    "prepare_adjust_shared_resource_cost": "adjust_shared_resource_cost",
    "prepare_meeting_minute_manage": "meeting_minute_manage",
}
