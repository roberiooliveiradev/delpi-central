"""Approved-specialist registry and governance rules — C3-MCP-INTEROP-01.

Catalog ownership lives in the remote specialists (ledger §6.109): each
owner advertises its capabilities through ``tools/list`` and types them
with ``_meta["delpi/toolClass"]``. DÉLIA keeps NO mirror of remote tool
names — this module holds only DÉLIA-owned governance:

  * the approved-specialist registry (identity/owner refs);
  * the interactive phase class gate (DISCOVERY | READ invocable;
    PREPARE/ACT/UNKNOWN blocked);
  * the provider-neutral mapping from owner-typed class to the
    SpecialistOperationClass vocabulary.

Remote metadata (descriptions, annotations like ``readOnlyHint``,
securitySchemes, titles) is untrusted data and can never grant
permission. The owner-typed class is trusted for classification only —
invocation additionally requires the matching DÉLIA policy binding.
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
# longer gate invocation. What remains DÉLIA-owned policy:
#
#   * the approved-specialist registry above (identity/owner refs) and
#     the configured connection approval (DELIA_MCP_*_ENABLED);
#   * the class/phase gate below — which owner-typed classes may be
#     invoked under the current interactive policy;
#   * fail-closed unknown-specialist / unadvertised-capability checks.
#
# CURRENT_INTERACTIVE_INVOCABLE_CLASSES = DISCOVERY | READ
# (ANALYSIS already projects as READ via _OWNER_CLASS_MAP).
# PREPARE/ACT are writes — visible in the projection, never invocable
# here. UNKNOWN (absent/invalid owner class) is never invocable.
INTERACTIVE_INVOCABLE_CLASSES: frozenset[SpecialistOperationClass] = (
    frozenset(
        {
            SpecialistOperationClass.DISCOVERY,
            SpecialistOperationClass.READ,
        }
    )
)


def invocable_in_interactive_phase(
    operation_class: SpecialistOperationClass,
) -> bool:
    """Current interactive class gate: DISCOVERY and READ only.

    Class eligibility is orchestration policy, not permission — the
    specialist/domain authorities still enforce live AuthZ downstream.
    """
    return operation_class in INTERACTIVE_INVOCABLE_CLASSES
