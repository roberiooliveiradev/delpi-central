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
surface (DISCOVERY/READ/ANALYSIS/PREPARE/ACT) is eligible for
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


# Single governed source for approved specialists (doc 60):
# (display_name, owner_ref, keycloak resource client_id, resource audience).
# Infrastructure derives its MCP connection profiles from this identity;
# no second registry may repeat the specialist set.
_SPECIALIST_IDENTITY: dict[str, tuple[str, str, str, str]] = {
    "davi": (
        "DAVI", "api-delpi", "mcp-api-delpi",
        "https://minhadelpi.com.br/apps/api-delpi/mcp",
    ),
    "teo": (
        "TEO", "transformometro-api", "mcp-transformometro",
        "https://minhadelpi.com.br/apps/transformometro-api/mcp",
    ),
    "vista": (
        "VISTA", "tv-dashboard-api", "mcp-tv-dashboard",
        "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp",
    ),
    "caio": (
        "CAIO", "commercial-api", "mcp-commercial",
        "https://minhadelpi.com.br/apps/commercial-api/mcp",
    ),
    "clara": (
        "CLARA", "controllership-finance-api",
        "mcp-controllership-finance",
        "https://minhadelpi.com.br/apps/controllership-finance-api/mcp",
    ),
    "suri": (
        "SURI", "supplies-mcp", "mcp-supplies",
        "https://minhadelpi.com.br/apps/supplies-api/mcp",
    ),
    "eva": (
        "EVA", "engineering-api", "mcp-engineering",
        "https://minhadelpi.com.br/apps/engineering-api/mcp",
    ),
}

APPROVED_SPECIALIST_IDS = frozenset(_SPECIALIST_IDENTITY)


def specialist_ref_or_none(
    specialist_id: str,
    *,
    display_name: str | None = None,
    owner_ref: str | None = None,
) -> SpecialistRef | None:
    """Return SpecialistRef for a known or Core-governed provider.

    The seven DELPI specialists remain the canonical identity table.
    Additional Core-approved providers may be admitted when
    ``display_name`` and ``owner_ref`` are supplied by the governed
    connection profile (R1-RW04) — never from tool metadata alone.
    """
    sid = str(specialist_id or "").strip().lower()
    identity = _SPECIALIST_IDENTITY.get(sid)
    if identity is not None:
        return SpecialistRef(
            specialist_id=sid,
            display_name=identity[0],
            owner_ref=identity[1],
        )
    display = str(display_name or "").strip()
    owner = str(owner_ref or "").strip()
    if sid and display and owner:
        return SpecialistRef(
            specialist_id=sid,
            display_name=display,
            owner_ref=owner,
        )
    return None


# Provider-neutral mapping from the owner-typed DELPI ToolClass wire
# vocabulary to the DÉLIA semantic class. ANALYSIS (non-persisting
# owner analysis) is first-class — it stays ANALYSIS so a bounded
# ANALYSIS -> PREPARE continuation is expressible; its outcome remains
# OBSERVATION evidence, never FACT. Anything else -> UNKNOWN
# (discoverable, never invocable).
_OWNER_CLASS_MAP: dict[str, SpecialistOperationClass] = {
    "DISCOVERY": SpecialistOperationClass.DISCOVERY,
    "READ": SpecialistOperationClass.READ,
    "ANALYSIS": SpecialistOperationClass.ANALYSIS,
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
# GOVERNED_INVOCABLE_CLASSES = DISCOVERY | READ | ANALYSIS | PREPARE |
# ACT. A class is orchestration eligibility — never permission.
# UNKNOWN (absent or invalid owner class) is never invocable.
INTERACTIVE_INVOCABLE_CLASSES: frozenset[SpecialistOperationClass] = (
    frozenset(
        {
            SpecialistOperationClass.DISCOVERY,
            SpecialistOperationClass.READ,
            SpecialistOperationClass.ANALYSIS,
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
