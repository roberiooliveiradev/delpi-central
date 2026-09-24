"""Canonical confirmation / commit_now policy for TÉO governed writes.

Single source of truth for GPT Actions and MCP. Adapters must not fork this.
"""

from __future__ import annotations

from typing import Literal

PolicyVerdict = Literal["allow", "deny"]

# Entity record operations (prepare_record_change)
_ENTITY_COMMIT_NOW: dict[str, PolicyVerdict] = {
    "create": "allow",
    "update": "allow",
    "duplicate": "allow",
    "delete": "deny",
}

# Orchestrator capability names
_CAPABILITY_COMMIT_NOW: dict[str, PolicyVerdict] = {
    "create_record": "allow",
    "update_record": "allow",
    "duplicate_record": "allow",
    "delete_record": "deny",
    "commit_improvement_package": "allow",
    "adjust_shared_resource_cost": "allow",
    "activate_revision": "deny",
    "recalculate_dashboard": "deny",
    "meeting_minute_workflow": "deny",
    "manage_evidence": "deny",
    "meeting_minute_manage": "deny",
}

# Workflow ids as exposed on capability_surface
_WORKFLOW_COMMIT_NOW: dict[str, PolicyVerdict] = {
    "improvement_package": "allow",
    "adjust_shared_resource_cost": "allow",
    "activate_revision": "deny",
    "recalculate_dashboard": "deny",
    "meeting_minute_workflow": "deny",
    "manage_evidence": "deny",
    "meeting_minute_manage": "deny",
}


def allows_commit_now_for_entity_operation(operation: str) -> bool:
    op = str(operation or "").strip().lower()
    return _ENTITY_COMMIT_NOW.get(op) == "allow"


def allows_commit_now_for_capability(capability: str) -> bool:
    cap = str(capability or "").strip()
    return _CAPABILITY_COMMIT_NOW.get(cap) == "allow"


def allows_commit_now_for_workflow(workflow_id: str) -> bool:
    wid = str(workflow_id or "").strip()
    return _WORKFLOW_COMMIT_NOW.get(wid) == "allow"


def confirmation_policy_label_for_entity_operation(operation: str) -> str:
    if allows_commit_now_for_entity_operation(operation):
        return "commit_now_allowed_additive"
    return "explicit_user_confirmation_before_commit"


def confirmation_policy_label_for_workflow(workflow_id: str) -> str:
    if allows_commit_now_for_workflow(workflow_id):
        return "commit_now_allowed_additive"
    return "explicit_user_confirmation_before_commit"
