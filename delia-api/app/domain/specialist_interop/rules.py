"""Approved-specialist registry and governance rules — C3-MCP-INTEROP-01.

Catalog ownership lives in the remote specialists (ledger §6.109): each
owner advertises its capabilities through ``tools/list`` and types them
with ``_meta["delpi/toolClass"]``. DÉLIA keeps NO mirror of remote tool
names — this module holds only DÉLIA-owned governance:

  * the approved-specialist registry (identity/owner refs);
  * the bounded DISCOVERY invocation bindings;
  * the task-scoped governed READ authorizations;
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


# DÉLIA approval policy (not a catalog mirror): the bounded set of
# DISCOVERY-class capabilities DÉLIA may invoke through the C3
# foundation. A remote tool projecting DISCOVERY without a binding here
# is discoverable but not invocable — owner typing never self-grants.
GOVERNED_DISCOVERY_BINDINGS: frozenset[tuple[str, str]] = frozenset(
    {
        ("davi", "discover_delpi_information"),
        ("teo", "get_catalog"),
        ("vista", "get_catalog"),
    }
)


def discovery_binding_allowed(specialist_id: str, remote_name: str) -> bool:
    """True only for the DÉLIA-approved DISCOVERY invocation bindings."""
    return (
        str(specialist_id or "").strip().lower(),
        str(remote_name or "").strip(),
    ) in GOVERNED_DISCOVERY_BINDINGS


def invocable_in_foundation(operation_class: SpecialistOperationClass) -> bool:
    """C3 foundation class gate: DISCOVERY/CATALOG only.

    Class eligibility alone is not invocation permission — a DISCOVERY
    class still requires a GOVERNED_DISCOVERY_BINDINGS entry, and READ
    requires the separate C4 authorization. PREPARE/ACT are writes.
    """
    return operation_class is SpecialistOperationClass.DISCOVERY


# C4-MCP-GOVERNED-READS-01/02: the only task-scoped bounded READ
# authorizations. Maps (specialist, remote capability) -> the exact set
# of governed action ids DÉLIA orchestration may execute. This is
# DÉLIA orchestration policy, not specialist business authority — DAVI
# still decides candidate eligibility, API DELPI still enforces Product
# Master AuthZ, and transformometro-api still enforces dashboard view
# access. Everything outside this table stays phase-gated.
GOVERNED_READ_ACTIONS: dict[tuple[str, str], frozenset[str]] = {
    ("davi", "execute_delpi_information"): frozenset({"search_products"}),
    ("teo", "analyze"): frozenset({"gpt_analyze"}),
}

# Canonical single binding for the first slice — the only place
# specialist identity for the DAVI governed read may be named.
GOVERNED_READ_SPECIALIST = "davi"
GOVERNED_READ_DISCOVERY_CAPABILITY = "discover_delpi_information"
GOVERNED_READ_EXECUTE_CAPABILITY = "execute_delpi_information"
GOVERNED_READ_ACTION_ID = "search_products"

# C4-MCP-GOVERNED-READS-02: canonical binding for the TÉO dashboard
# read. `gpt_analyze` is the owner's stable operation identifier for the
# MCP `analyze` capability — it identifies the binding, it grants
# nothing.
GOVERNED_READ_TEO_SPECIALIST = "teo"
GOVERNED_READ_TEO_CAPABILITY = "analyze"
GOVERNED_READ_TEO_ACTION_ID = "gpt_analyze"


def governed_read_action_allowed(
    specialist_id: str, remote_name: str, action_id: str | None
) -> bool:
    """Bounded C4 gate: True only for the explicitly authorized tuple."""
    allowed = GOVERNED_READ_ACTIONS.get(
        (
            str(specialist_id or "").strip().lower(),
            str(remote_name or "").strip(),
        )
    )
    if not allowed or action_id is None:
        return False
    return str(action_id).strip() in allowed


def enabled_governed_read_tuples(
    *,
    davi_product_read: bool = False,
    teo_dashboard_analyze: bool = False,
) -> frozenset[tuple[str, str, str]]:
    """The exact governed READ tuples switched on by trusted config.

    Each task-scoped flag contributes exactly its own tuple; no flag
    ever widens another binding's authorization surface.
    """
    enabled: set[tuple[str, str, str]] = set()
    if davi_product_read:
        enabled.add(
            (
                GOVERNED_READ_SPECIALIST,
                GOVERNED_READ_EXECUTE_CAPABILITY,
                GOVERNED_READ_ACTION_ID,
            )
        )
    if teo_dashboard_analyze:
        enabled.add(
            (
                GOVERNED_READ_TEO_SPECIALIST,
                GOVERNED_READ_TEO_CAPABILITY,
                GOVERNED_READ_TEO_ACTION_ID,
            )
        )
    return frozenset(enabled)
