"""Approved-specialist registry and classification rules — C3-MCP-INTEROP-01.

The canonical DÉLIA-side allowlist for the C3 interoperability slice. Only
DAVI, TÉO, and VISTA are approved; only the remote capability names listed
here are classifiable, and only DISCOVERY-class capabilities are invocable
while C4 read execution is not authorized.

Classification is DÉLIA-owned: remote tool metadata (descriptions,
annotations like ``readOnlyHint``, securitySchemes) is untrusted data and
can never elevate a capability's class. Unknown specialist or unknown
remote name fails closed.
"""

from __future__ import annotations

from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
    SpecialistRef,
)


# DÉLIA-owned remote capability classification per approved specialist.
# Mirrors each owner's authoritative TOOL_CLASS contract:
#   DAVI  — api-delpi/app/interface/mcp (discover + catalog-fixed execute)
#   TÉO   — transformometro-api TOOL_CLASS (ANALYSIS -> READ here)
#   VISTA — tv-dashboard-api TOOL_CLASS
SPECIALIST_CAPABILITY_CLASSES: dict[str, dict[str, SpecialistOperationClass]] = {
    "davi": {
        "discover_delpi_information": SpecialistOperationClass.DISCOVERY,
        "execute_delpi_information": SpecialistOperationClass.READ,
    },
    "teo": {
        "get_catalog": SpecialistOperationClass.DISCOVERY,
        "get_my_context": SpecialistOperationClass.READ,
        "get_methodology_guide": SpecialistOperationClass.READ,
        "get_process_context": SpecialistOperationClass.READ,
        "analyze": SpecialistOperationClass.READ,
        "search_records": SpecialistOperationClass.READ,
        "get_record": SpecialistOperationClass.READ,
        "list_evidence": SpecialistOperationClass.READ,
        "get_process_timeline": SpecialistOperationClass.READ,
        "meeting_minute_read": SpecialistOperationClass.READ,
        "get_diagnostic": SpecialistOperationClass.READ,
        "list_diagnostics_by_revision": SpecialistOperationClass.READ,
        "generate_from_transcript": SpecialistOperationClass.READ,
        "prepare_record_change": SpecialistOperationClass.PREPARE,
        "prepare_activate_revision": SpecialistOperationClass.PREPARE,
        "prepare_recalculate_dashboard": SpecialistOperationClass.PREPARE,
        "prepare_meeting_minute_workflow": SpecialistOperationClass.PREPARE,
        "prepare_improvement_package": SpecialistOperationClass.PREPARE,
        "prepare_manage_evidence": SpecialistOperationClass.PREPARE,
        "prepare_adjust_shared_resource_cost": SpecialistOperationClass.PREPARE,
        "prepare_meeting_minute_manage": SpecialistOperationClass.PREPARE,
        "prepare_create_diagnostic": SpecialistOperationClass.PREPARE,
        "prepare_manage_diagnostic": SpecialistOperationClass.PREPARE,
        "commit_proposal": SpecialistOperationClass.ACT,
    },
    "vista": {
        "get_catalog": SpecialistOperationClass.DISCOVERY,
        "list_playlists": SpecialistOperationClass.READ,
        "get_playlist_context": SpecialistOperationClass.READ,
        "search_data_routes": SpecialistOperationClass.READ,
        "inspect_data_model": SpecialistOperationClass.READ,
        "preview_data_model": SpecialistOperationClass.READ,
        "prepare_change": SpecialistOperationClass.PREPARE,
        "commit_proposal": SpecialistOperationClass.ACT,
    },
}

_SPECIALIST_IDENTITY: dict[str, tuple[str, str]] = {
    "davi": ("DAVI", "api-delpi"),
    "teo": ("TEO", "transformometro-api"),
    "vista": ("VISTA", "tv-dashboard-api"),
}

APPROVED_SPECIALIST_IDS = frozenset(SPECIALIST_CAPABILITY_CLASSES)


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


def operation_class_for(
    specialist_id: str, remote_name: str
) -> SpecialistOperationClass | None:
    """DÉLIA-owned class for a remote capability; None when unknown.

    Remote metadata claims are never consulted — a tool that calls itself
    read-only while the registry classifies it as PREPARE/ACT stays blocked.
    """
    catalog = SPECIALIST_CAPABILITY_CLASSES.get(
        str(specialist_id or "").strip().lower()
    )
    if catalog is None:
        return None
    return catalog.get(str(remote_name or "").strip())


def invocable_in_foundation(operation_class: SpecialistOperationClass) -> bool:
    """C3 foundation invocation gate: DISCOVERY/CATALOG only.

    READ requires the separate C4 authorization; PREPARE/ACT are writes.
    """
    return operation_class is SpecialistOperationClass.DISCOVERY
