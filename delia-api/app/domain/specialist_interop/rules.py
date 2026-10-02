"""Approved-specialist registry and governance rules — C3-MCP-INTEROP-01.

Catalog ownership lives in the remote specialists (ledger §6.109): each
owner advertises its capabilities through ``tools/list`` and types them
with ``_meta["delpi/toolClass"]``. DÉLIA keeps NO mirror of remote tool
names — this module holds only DÉLIA-owned governance:

  * the approved-specialist registry (identity/owner refs);
  * the operation-class gate (all owner-typed known classes are
    governed-invocable; UNKNOWN is discoverable but never invocable);
  * the provider-neutral mapping from owner-typed class to the
    SpecialistOperationClass vocabulary.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126): DÉLIA
is the orchestrator of approved MCP specialists — the full advertised
surface (DISCOVERY/READ/ANALYSIS-as-READ/PREPARE/ACT) is eligible for
orchestration under generic write governance. Invocable class is
orchestration eligibility, never permission: live Core AuthZ,
specialist/domain authority, schema validation, confirmation when the
owner contract requires it, idempotency and owner-authoritative
postcondition all still apply downstream.

Remote metadata (descriptions, annotations like ``readOnlyHint``,
securitySchemes, titles) is untrusted data and can never grant
permission. The owner-typed class is trusted for classification only.
Unknown specialist, unadvertised remote name, or unclassifiable
operation class fails closed.
"""

from __future__ import annotations

from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistRef,
)


_SPECIALIST_IDENTITY: dict[str, tuple[str, str]] = {
    "davi": ("DAVI", "api-delpi"),
    "teo": ("TEO", "transformometro-api"),
    "vista": ("VISTA", "tv-dashboard-api"),
}

APPROVED_SPECIALIST_IDS = frozenset(_SPECIALIST_IDENTITY)


def specialist_ref_or_none(specialist_id: str) -> SpecialistRef | None:
    """Return the canonical SpecialistRef for an approved id, else None."""
    identity = _SPECIALIST_IDENTITY.get(str(specialist_id or "").strip().lower())
    if identity is None:
        return None
    return SpecialistRef(
        specialist_id=str(specialist_id).strip().lower(),
        display_name=identity[0],
        owner_ref=identity[1],
    )


# Provider-neutral mapping from the owner-typed DELPI ToolClass wire
# vocabulary to the DÉLIA semantic class. ANALYSIS (non-persisting
# analysis) projects as READ. Anything else -> UNKNOWN (discoverable,
# never invocable).
_OWNER_CLASS_MAP: dict[str, SpecialistOperationClass] = {
    "DISCOVERY": SpecialistOperationClass.DISCOVERY,
    "READ": SpecialistOperationClass.READ,
    "ANALYSIS": SpecialistOperationClass.READ,
    "PREPARE": SpecialistOperationClass.PREPARE,
    "ACT": SpecialistOperationClass.ACT,
}


def operation_class_from_owner(raw: object) -> SpecialistOperationClass:
    """Project the owner-typed tool class; UNKNOWN when absent/invalid.

    ``raw`` is the owner-emitted ``_meta["delpi/toolClass"]`` value —
    trusted for classification only, never for permission.
    """
    if not isinstance(raw, str):
        return SpecialistOperationClass.UNKNOWN
    return _OWNER_CLASS_MAP.get(
        raw.strip().upper(), SpecialistOperationClass.UNKNOWN
    )


# ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02 (ledger §6.118): the specialist
# owns its capability surface end-to-end — existence, naming, class and
# availability are live owner data from ``tools/list``, not DÉLIA-local
# state. The former second authority is superseded:
# GOVERNED_DISCOVERY_BINDINGS, GOVERNED_READ_ACTIONS,
# enabled_governed_read_tuples and the DELIA_C4_*_ENABLED switches no
# longer gate invocation.
#
# ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 (ledger §6.126):
# PREPARE/ACT are governed-invocable — the READ-only class gate is
# superseded. What remains DÉLIA-owned policy:
#
#   * the approved-specialist registry above (identity/owner refs) and
#     the configured connection approval (DELIA_MCP_*_ENABLED);
#   * the class gate below — every owner-typed known class is eligible
#     for orchestration; writes still pass the generic write
#     governance chain (live AuthZ, owner/domain authority,
#     confirmation when required, idempotency, postcondition);
#   * fail-closed unknown-specialist / unadvertised-capability /
#     UNKNOWN-class checks.
#
# GOVERNED_INVOCABLE_CLASSES = DISCOVERY | READ | PREPARE | ACT
# (ANALYSIS projects as READ via _OWNER_CLASS_MAP). A class is
# orchestration eligibility — never permission. UNKNOWN (absent or
# invalid owner class) is never invocable.
INTERACTIVE_INVOCABLE_CLASSES: frozenset[SpecialistOperationClass] = (
    frozenset(
        {
            SpecialistOperationClass.DISCOVERY,
            SpecialistOperationClass.READ,
            SpecialistOperationClass.PREPARE,
            SpecialistOperationClass.ACT,
        }
    )
)


def invocable_in_interactive_phase(
    operation_class: SpecialistOperationClass,
) -> bool:
    """Class gate: every known owner-typed class is governed-invocable.

    Class eligibility is orchestration policy, not permission — the
    specialist/domain authorities still enforce live AuthZ downstream,
    and write-class invocations pass generic write governance
    (confirmation/idempotency/owner-verified postcondition) in the
    orchestration layer.
    """
    return operation_class in INTERACTIVE_INVOCABLE_CLASSES
