"""Capability descriptors for TÉO GPT Actions / MCP catalog projection.

Transport-agnostic metadata (entity / workflow / analysis). Not AuthZ authority.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.entities import (
    ENTITY_CAPABILITIES,
    ENTITY_DESCRIPTIONS,
    GptEntity,
)


# Fields clients must never set via prepare_record_change changes/data.
SERVER_OWNED_FIELDS: dict[str, frozenset[str]] = {
    "process_document": frozenset(
        {
            "id",
            "document_id",
            "created_by_user_id",
            "updated_by_user_id",
            "created_at",
            "updated_at",
            "deleted_at",
        }
    ),
    "process": frozenset({"processo_id", "created_at", "updated_at", "deletado"}),
    "instance": frozenset({"instancia_id", "created_at", "updated_at", "deletado"}),
    "revision": frozenset({"revisao_id", "created_at", "updated_at", "deletado"}),
    "meeting_minute": frozenset({"id", "created_at", "updated_at", "deleted_at"}),
}

# Allowlisted search filters per entity (generic READ). Unknown filter → fail closed.
ENTITY_FILTERABLE_FIELDS: dict[str, frozenset[str]] = {
    "process": frozenset(
        {"filial_id", "setor_id", "status", "familia_processo", "q"}
    ),
    "instance": frozenset({"parent_id"}),
    "revision": frozenset({"parent_id", "instance_id"}),
    "measurement": frozenset({"parent_id"}),
    "investment": frozenset({"parent_id"}),
    "resource_cost": frozenset({"parent_id"}),
    "resource_link": frozenset({"parent_id"}),
    "meeting_minute": frozenset({"unit_code", "status", "q"}),
    "process_document": frozenset({"parent_id", "q"}),
    "branch": frozenset(),
    "department": frozenset({"filial_id"}),
    "shared_resource": frozenset(),
}

RECORD_OPERATIONS = frozenset({"create", "update", "delete", "duplicate"})

OPERATION_TO_CAPABILITY = {
    "create": "create_record",
    "update": "update_record",
    "delete": "delete_record",
    "duplicate": "duplicate_record",
}


def build_capability_surface_catalog() -> dict[str, Any]:
    """Rich descriptors projected inside gpt_get_catalog (additive)."""
    entities: list[dict[str, Any]] = []
    for entity in GptEntity:
        caps = ENTITY_CAPABILITIES.get(entity, frozenset())
        write_ops = sorted(
            op
            for op, need in (
                ("create", "create"),
                ("update", "update"),
                ("delete", "delete"),
                ("duplicate", "duplicate"),
            )
            if need in caps
        )
        read_ops = sorted(
            op for op in ("search", "get") if op in caps
        )
        entities.append(
            {
                "id": entity.value,
                "kind": "entity",
                "owner": "transformometro-api",
                "description": ENTITY_DESCRIPTIONS.get(entity, entity.value),
                "read_operations": read_ops,
                "write_operations": write_ops,
                "filterable_fields": sorted(
                    ENTITY_FILTERABLE_FIELDS.get(entity.value, frozenset())
                ),
                "server_owned_fields": sorted(
                    SERVER_OWNED_FIELDS.get(entity.value, frozenset())
                ),
                "prepare_act_policy": "prepare_record_change → commit_proposal"
                if write_ops
                else "read_only",
                "confirmation_policy": "explicit_user_confirmation_before_commit"
                if write_ops
                else None,
                "permission_metadata": {
                    "note": "Catalog is not AuthZ. Backend enforces transformometro.access/manage and domain rules.",
                    "typical_gate": "transformometro.access",
                },
            }
        )

    workflows = [
        {
            "id": "activate_revision",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Activate a revision as the operational scenario (overwrite current).",
            "read_write": "WRITE",
            "prepare_operation": "gpt_activate_revision",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "improvement_package",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Nested process+instance+revision+measurement package.",
            "read_write": "WRITE",
            "prepare_operation": "gpt_validate_improvement_package",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "meeting_minute_workflow",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "send / finalize / cancel meeting minute transitions.",
            "read_write": "WRITE",
            "prepare_operation": "gpt_meeting_minute_workflow",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "manage_evidence",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Link/metadata evidence (binary upload remains UI-only).",
            "read_write": "WRITE",
            "prepare_operation": "gpt_manage_evidence",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "adjust_shared_resource_cost",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Business cost adjustment for shared resources.",
            "read_write": "WRITE",
            "prepare_operation": "gpt_adjust_shared_resource_cost",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "recalculate_dashboard",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Recalculate materialised dashboard cache.",
            "read_write": "WRITE",
            "prepare_operation": "gpt_recalculate_dashboard",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative",
        },
        {
            "id": "meeting_minute_manage",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Meeting-minute extras (reads + governed writes like resend).",
            "read_write": "MIXED",
            "prepare_operation": "gpt_meeting_minute_manage",
            "commit_via": "gpt_commit_proposal",
            "confirmation_requirement": True,
            "read_back_policy": "authoritative_when_write",
        },
    ]

    analyses = [
        {
            "id": "analyze",
            "kind": "analysis",
            "owner": "transformometro-api",
            "description": "Dashboard KPI views (meta/summary/processes/instances/rows).",
            "read_only": True,
            "operation": "gpt_analyze",
        },
        {
            "id": "methodology_guide",
            "kind": "analysis",
            "owner": "transformometro-api",
            "description": "Method playbooks (not domain facts / AuthZ / writes).",
            "read_only": True,
            "operation": "gpt_get_methodology_guide",
        },
        {
            "id": "process_timeline",
            "kind": "analysis",
            "owner": "transformometro-api",
            "description": "Process audit timeline.",
            "read_only": True,
            "operation": "gpt_get_process_timeline",
        },
    ]

    return {
        "surface_version": "teo-gpt-actions-v2",
        "proposal_model": {
            "prepare_then_commit": True,
            "opaque_proposal_handle": True,
            "commit_operation": "gpt_commit_proposal",
            "ttl_seconds_default": 900,
            "store": "in_process",
            "store_residual": "ACCEPTED_WITH_RESIDUAL for multi-replica",
            "note": (
                "commit_proposal is NOT a generic proxy: it only executes "
                "server-side proposals produced by governed PREPARE."
            ),
        },
        "not_exposed_by_design": ["tm_task", "interaction_room", "process_workspace"],
        "entities": entities,
        "workflows": workflows,
        "analyses": analyses,
        "delia_projection_hint": {
            "status": "PLANNED",
            "consume": "capability_surface entities/workflows/analyses",
            "do_not": "import Transformômetro internals or reimplement business rules",
        },
    }
