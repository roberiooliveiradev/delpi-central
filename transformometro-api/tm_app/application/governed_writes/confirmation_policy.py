"""Canonical write-execution policy for TÉO governed writes.

Single source of truth for GPT Actions and MCP. Adapters must not fork this.

Semantic model (TEO-CANONICAL-WRITE-EXECUTION-POLICY-04):

- ``auto_act`` — non-destructive write: execute directly after governed
  PREPARE. A direct user request is sufficient intent; no conversational
  confirmation round-trip. ACT still requires AuthZ, validation, proposal
  integrity, audit and authoritative read-back.
- ``confirm_before_act`` — destructive/consequential write: show the exact
  prepared change and require ONE explicit user confirmation before ACT.

Semantic deduplication (TEO-WRITE-POLICY-FINAL-DEDUPLICATION-05):

- ``_WRITE_POLICIES`` holds ONE ``WritePolicyRecord`` per semantic write
  capability — the policy value appears exactly once. Transport/API names
  (orchestrator capability, workflow id, entity operation) are ALIASES on
  the same record; the derived indexes map alias → record, never
  alias → policy value. One business decision = one edit.

Transport mechanics are NOT the policy: Actions ``commit_now`` is only the
Actions adapter's way of implementing ``auto_act``; MCP PREPARE stays pure
and ``commit_proposal`` remains the ACT path. Destructiveness is classified
explicitly per semantic capability — never inferred from verbs or transport.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

ExecutionPolicy = Literal["auto_act", "confirm_before_act"]

AUTO_ACT: ExecutionPolicy = "auto_act"
CONFIRM_BEFORE_ACT: ExecutionPolicy = "confirm_before_act"


@dataclass(frozen=True)
class WritePolicyRecord:
    """One semantic write capability and its canonical execution policy.

    ``capability`` is the orchestrator capability name (the authoritative
    runtime identity); ``workflow_id`` / ``entity_operation`` are catalog /
    entity-CRUD aliases onto the same semantic decision.
    """

    semantic_id: str
    execution_policy: ExecutionPolicy
    capability: str
    workflow_id: str | None = None
    entity_operation: str | None = None


# --- Canonical semantic policy table ------------------------------------------
# THE only place policy VALUES are defined. Classified by business effect —
# additive writes auto-act; destructive/consequential writes confirm first.
_WRITE_POLICIES: tuple[WritePolicyRecord, ...] = (
    # Entity record CRUD — additive operations auto-act.
    WritePolicyRecord(
        "record.create", AUTO_ACT, "create_record", entity_operation="create"
    ),
    WritePolicyRecord(
        "record.update", AUTO_ACT, "update_record", entity_operation="update"
    ),
    WritePolicyRecord(
        "record.duplicate",
        AUTO_ACT,
        "duplicate_record",
        entity_operation="duplicate",
    ),
    WritePolicyRecord(
        "record.delete",
        CONFIRM_BEFORE_ACT,
        "delete_record",
        entity_operation="delete",
    ),
    # Compound multi-entity write; may supersede the active scenario
    # (activate_scenario) and recalculate materialized state.
    WritePolicyRecord(
        "improvement_package.commit",
        CONFIRM_BEFORE_ACT,
        "commit_improvement_package",
        workflow_id="improvement_package",
    ),
    # Append-only reajuste register; does not overwrite state.
    WritePolicyRecord(
        "shared_resource_cost.adjust",
        AUTO_ACT,
        "adjust_shared_resource_cost",
        workflow_id="adjust_shared_resource_cost",
    ),
    # Supersedes the operational scenario revision (state loss).
    WritePolicyRecord(
        "revision.activate",
        CONFIRM_BEFORE_ACT,
        "activate_revision",
        workflow_id="activate_revision",
    ),
    # Overwrites materialized dashboard state (consequential mass write).
    WritePolicyRecord(
        "dashboard.recalculate",
        CONFIRM_BEFORE_ACT,
        "recalculate_dashboard",
        workflow_id="recalculate_dashboard",
    ),
    # send / finalize / cancel — irreversible lifecycle transitions.
    WritePolicyRecord(
        "meeting_minute.workflow",
        CONFIRM_BEFORE_ACT,
        "meeting_minute_workflow",
        workflow_id="meeting_minute_workflow",
    ),
    # Includes evidence delete; classified at capability granularity.
    WritePolicyRecord(
        "evidence.manage",
        CONFIRM_BEFORE_ACT,
        "manage_evidence",
        workflow_id="manage_evidence",
    ),
    # resend = external communication side effect; version creates.
    WritePolicyRecord(
        "meeting_minute.manage",
        CONFIRM_BEFORE_ACT,
        "meeting_minute_manage",
        workflow_id="meeting_minute_manage",
    ),
    # Diagnostic V1 (MCP-native): create is a pure additive root entity.
    WritePolicyRecord("diagnostic.create", AUTO_ACT, "create_diagnostic"),
    # manage actions include validate/reject/supersede lifecycle transitions.
    WritePolicyRecord(
        "diagnostic.manage", CONFIRM_BEFORE_ACT, "manage_diagnostic"
    ),
)


# --- Derived alias indexes (alias → record; NEVER alias → policy value) -------
def _build_indexes(
    records: Iterable[WritePolicyRecord],
) -> tuple[
    dict[str, WritePolicyRecord],
    dict[str, WritePolicyRecord],
    dict[str, WritePolicyRecord],
]:
    by_capability: dict[str, WritePolicyRecord] = {}
    by_workflow: dict[str, WritePolicyRecord] = {}
    by_entity_op: dict[str, WritePolicyRecord] = {}
    for rec in records:
        by_capability[rec.capability] = rec
        if rec.workflow_id is not None:
            by_workflow[rec.workflow_id] = rec
        if rec.entity_operation is not None:
            by_entity_op[rec.entity_operation.lower()] = rec
    return by_capability, by_workflow, by_entity_op


_BY_CAPABILITY, _BY_WORKFLOW, _BY_ENTITY_OPERATION = _build_indexes(
    _WRITE_POLICIES
)


def write_policy_records() -> tuple[WritePolicyRecord, ...]:
    """Every semantic write-policy record (the canonical table)."""
    return _WRITE_POLICIES


def policy_record_for_capability(
    capability: str, *, records: Iterable[WritePolicyRecord] | None = None
) -> WritePolicyRecord | None:
    """The semantic policy record bound to an orchestrator capability."""
    table = _build_indexes(records)[0] if records is not None else _BY_CAPABILITY
    return table.get(str(capability or "").strip())


class UnknownPolicyError(ValueError):
    """Raised when a projection asks for a policy that is not classified."""


def execution_policy_for_entity_operation(
    operation: str,
    *,
    records: Iterable[WritePolicyRecord] | None = None,
) -> ExecutionPolicy:
    """Canonical policy for a prepare_record_change operation.

    Fail closed: an unknown operation resolves to ``confirm_before_act``
    (the safest semantic — explicit confirmation is never a security hole).
    """
    op = str(operation or "").strip().lower()
    table = (
        _build_indexes(records)[2] if records is not None else _BY_ENTITY_OPERATION
    )
    rec = table.get(op)
    return rec.execution_policy if rec is not None else CONFIRM_BEFORE_ACT


def execution_policy_for_capability(
    capability: str,
    *,
    records: Iterable[WritePolicyRecord] | None = None,
) -> ExecutionPolicy:
    """Canonical policy for an orchestrator write capability.

    Fail closed: unknown/unclassified capabilities require confirmation.
    """
    rec = policy_record_for_capability(capability, records=records)
    return rec.execution_policy if rec is not None else CONFIRM_BEFORE_ACT


def execution_policy_for_workflow(
    workflow_id: str,
    *,
    records: Iterable[WritePolicyRecord] | None = None,
) -> ExecutionPolicy:
    """Canonical policy for a capability_surface workflow id.

    Fail closed: unknown workflows require confirmation.
    """
    wid = str(workflow_id or "").strip()
    table = _build_indexes(records)[1] if records is not None else _BY_WORKFLOW
    rec = table.get(wid)
    return rec.execution_policy if rec is not None else CONFIRM_BEFORE_ACT


def classified_write_capabilities() -> frozenset[str]:
    """Every material-write capability with an explicit canonical policy."""
    return frozenset(_BY_CAPABILITY)


def write_policy_id_for_capability(capability: str) -> str | None:
    """Semantic write-policy id bound to a capability (registry link)."""
    rec = policy_record_for_capability(capability)
    return rec.semantic_id if rec is not None else None


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
