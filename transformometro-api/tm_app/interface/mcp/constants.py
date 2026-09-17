"""Frozen TÉO MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. Do not rename for «TÉO».
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP (not chatgpt-transformometro).
MCP_PREDEFINED_CLIENT_ID = "mcp-transformometro"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/transformometro-api/mcp"

MCP_GATEWAY_ROOT = "/apps/transformometro-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# GPT Actions bridge remains available; MCP is the Plugin/Agent target.
GPT_ACTIONS_LIFECYCLE = "LEGACY_TRANSITIONAL_BRIDGE"

TEO_MCP_SURFACE = "FULL_CRUD"

# MCP tool name → GPT Actions operationId (parity map).
TOOL_TO_GPT_OPERATION: dict[str, str] = {
    "get_my_context": "gpt_get_my_context",
    "get_catalog": "gpt_get_catalog",
    "get_process_context": "gpt_get_process_context",
    "analyze": "gpt_analyze",
    "search_records": "gpt_search_records",
    "get_record": "gpt_get_record",
    "create_record": "gpt_create_record",
    "update_record": "gpt_update_record",
    "delete_record": "gpt_delete_record",
    "duplicate_record": "gpt_duplicate_record",
    "activate_revision": "gpt_activate_revision",
    "recalculate_dashboard": "gpt_recalculate_dashboard",
    "meeting_minute_workflow": "gpt_meeting_minute_workflow",
    "validate_improvement_package": "gpt_validate_improvement_package",
    "commit_improvement_package": "gpt_commit_improvement_package",
    "list_evidence": "gpt_list_evidence",
    "manage_evidence": "gpt_manage_evidence",
    "get_process_timeline": "gpt_get_process_timeline",
    "adjust_shared_resource_cost": "gpt_adjust_shared_resource_cost",
    "meeting_minute_manage": "gpt_meeting_minute_manage",
}

TOOL_CLASS: dict[str, str] = {
    "get_my_context": "READ",
    "get_catalog": "READ",
    "get_process_context": "READ",
    "analyze": "READ",
    "search_records": "READ",
    "get_record": "READ",
    "create_record": "ACT",
    "update_record": "ACT",
    "delete_record": "ACT",
    "duplicate_record": "ACT",
    "activate_revision": "ACT",
    "recalculate_dashboard": "ACT",
    "meeting_minute_workflow": "ACT",
    "validate_improvement_package": "PREPARE",
    "commit_improvement_package": "ACT",
    "list_evidence": "READ",
    "manage_evidence": "ACT",
    "get_process_timeline": "READ",
    "adjust_shared_resource_cost": "ACT",
    "meeting_minute_manage": "ACT",  # some actions READ-ish; manage surface is write-capable
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_TO_GPT_OPERATION.keys())
