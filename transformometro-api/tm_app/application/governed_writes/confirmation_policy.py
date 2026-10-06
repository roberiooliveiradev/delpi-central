"""Canonical write-execution policy for TÉO governed writes.

Single source of truth for GPT Actions and MCP. Adapters must not fork this.

Semantic model (TEO-CANONICAL-WRITE-EXECUTION-POLICY-04):

- ``auto_act`` — non-destructive write: execute directly after governed
  PREPARE. A direct user request is sufficient intent; no conversational
  confirmation round-trip. ACT still requires AuthZ, validation, proposal
  integrity, audit and authoritative read-back.
- ``confirm_before_act`` — destructive/consequential write: show the exact
  prepared change and require ONE explicit user confirmation before ACT.

Transport mechanics are NOT the policy: Actions ``commit_now`` is only the
Actions adapter's way of implementing ``auto_act``; MCP PREPARE stays pure
and ``commit_proposal`` remains the ACT path. Destructiveness is classified
explicitly per capability — never inferred from verbs or transport.
"""

from __future__ import annotations

from typing import Literal

ExecutionPolicy = Literal["auto_act", "confirm_before_act"]

AUTO_ACT: ExecutionPolicy = "auto_act"
CONFIRM_BEFORE_ACT: ExecutionPolicy = "confirm_before_act"

# --- Canonical classification -------------------------------------------------
# Entity record operations (prepare_record_change). Classified by business
# effect: create/update/duplicate are additive; delete removes state.
_ENTITY_EXECUTION_POLICY: dict[str, ExecutionPolicy] = {
    "create": AUTO_ACT,
    "update": AUTO_ACT,
    "duplicate": AUTO_ACT,
    "delete": CONFIRM_BEFORE_ACT,
}

# Orchestrator capability names → canonical execution policy.
_CAPABILITY_EXECUTION_POLICY: dict[str, ExecutionPolicy] = {
    "create_record": AUTO_ACT,
    "update_record": AUTO_ACT,
    "duplicate_record": AUTO_ACT,
    "delete_record": CONFIRM_BEFORE_ACT,
    # Compound multi-entity write; may supersede the active scenario
    # (activate_scenario) and recalculate materialized state.
    "commit_improvement_package": CONFIRM_BEFORE_ACT,
    # Append-only reajuste register; does not overwrite state.
    "adjust_shared_resource_cost": AUTO_ACT,
    # Supersedes the operational scenario revision (state loss).
    "activate_revision": CONFIRM_BEFORE_ACT,
    # Overwrites materialized dashboard state (consequential mass write).
    "recalculate_dashboard": CONFIRM_BEFORE_ACT,
    # send / finalize / cancel — irreversible lifecycle transitions.
    "meeting_minute_workflow": CONFIRM_BEFORE_ACT,
    # Includes evidence delete; classified at capability granularity.
    "manage_evidence": CONFIRM_BEFORE_ACT,
    # resend = external communication side effect; version creates.
    "meeting_minute_manage": CONFIRM_BEFORE_ACT,
    # Diagnostic V1 (MCP-native): create is a pure additive root entity.
    "create_diagnostic": AUTO_ACT,
    # manage actions include validate/reject/supersede lifecycle transitions.
    "manage_diagnostic": CONFIRM_BEFORE_ACT,
}

# Workflow ids as exposed on capability_surface.
_WORKFLOW_EXECUTION_POLICY: dict[str, ExecutionPolicy] = {
    "improvement_package": CONFIRM_BEFORE_ACT,
    "adjust_shared_resource_cost": AUTO_ACT,
    "activate_revision": CONFIRM_BEFORE_ACT,
    "recalculate_dashboard": CONFIRM_BEFORE_ACT,
    "meeting_minute_workflow": CONFIRM_BEFORE_ACT,
    "manage_evidence": CONFIRM_BEFORE_ACT,
    "meeting_minute_manage": CONFIRM_BEFORE_ACT,
}


class UnknownPolicyError(ValueError):
    """Raised when a projection asks for a policy that is not classified."""


def execution_policy_for_entity_operation(
    operation: str, *, policies: dict[str, ExecutionPolicy] | None = None
) -> ExecutionPolicy:
    """Canonical policy for a prepare_record_change operation.

    Fail closed: an unknown operation resolves to ``confirm_before_act``
    (the safest semantic — explicit confirmation is never a security hole).
    """
    op = str(operation or "").strip().lower()
    return (policies or _ENTITY_EXECUTION_POLICY).get(op, CONFIRM_BEFORE_ACT)


def execution_policy_for_capability(
    capability: str, *, policies: dict[str, ExecutionPolicy] | None = None
) -> ExecutionPolicy:
    """Canonical policy for an orchestrator write capability.

    Fail closed: unknown/unclassified capabilities require confirmation.
    """
    cap = str(capability or "").strip()
    return (policies or _CAPABILITY_EXECUTION_POLICY).get(cap, CONFIRM_BEFORE_ACT)


def execution_policy_for_workflow(
    workflow_id: str, *, policies: dict[str, ExecutionPolicy] | None = None
) -> ExecutionPolicy:
    """Canonical policy for a capability_surface workflow id.

    Fail closed: unknown workflows require confirmation.
    """
    wid = str(workflow_id or "").strip()
    return (policies or _WORKFLOW_EXECUTION_POLICY).get(wid, CONFIRM_BEFORE_ACT)


def classified_write_capabilities() -> frozenset[str]:
    """Every material-write capability with an explicit canonical policy."""
    return frozenset(_CAPABILITY_EXECUTION_POLICY)


def requires_user_confirmation(capability: str) -> bool:
    """True when the canonical policy demands an explicit confirmation."""
    return execution_policy_for_capability(capability) == CONFIRM_BEFORE_ACT


# --- Actions adapter compatibility (commit_now mechanism) --------------------
# ``commit_now`` is a GPT Actions transport mechanism that implements the
# canonical ``auto_act`` policy for additive single-shot writes. These
# helpers exist ONLY so the Actions adapter keeps its historical names;
# the canonical reasoning is ``execution_policy_*`` above.


def allows_commit_now_for_entity_operation(operation: str) -> bool:
    return execution_policy_for_entity_operation(operation) == AUTO_ACT


def allows_commit_now_for_capability(capability: str) -> bool:
    return execution_policy_for_capability(capability) == AUTO_ACT


def allows_commit_now_for_workflow(workflow_id: str) -> bool:
    return execution_policy_for_workflow(workflow_id) == AUTO_ACT


def confirmation_policy_label_for_entity_operation(operation: str) -> str:
    """Legacy Actions-vocabulary label — kept for callers on that surface."""
    if allows_commit_now_for_entity_operation(operation):
        return "commit_now_allowed_additive"
    return "explicit_user_confirmation_before_commit"


def confirmation_policy_label_for_workflow(workflow_id: str) -> str:
    """Legacy Actions-vocabulary label — kept for callers on that surface."""
    if allows_commit_now_for_workflow(workflow_id):
        return "commit_now_allowed_additive"
    return "explicit_user_confirmation_before_commit"


# --- Neutral semantic kinds (transport-agnostic) -----------------------------
# Canonical model stores the KIND; each transport projection renders its own
# label via capability_registry.confirmation_policy_label(kind, transport).
# The kind vocabulary IS the canonical execution policy.

ConfirmationKind = Literal["auto_act", "confirm_before_act"]


def confirmation_kind_for_entity_operation(operation: str) -> ConfirmationKind:
    return execution_policy_for_entity_operation(operation)


def confirmation_kind_for_workflow(workflow_id: str) -> ConfirmationKind:
    return execution_policy_for_workflow(workflow_id)
