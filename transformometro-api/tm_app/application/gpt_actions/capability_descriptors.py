"""Capability surface descriptors — transport-neutral canonical model.

Transport-agnostic metadata (entity / workflow / analysis). Not AuthZ
authority.

Architecture: ONE canonical semantic surface uses transport-neutral
capability names (the MCP tool names — they carry no transport prefix).
Each transport receives a derived projection:

- ``projection="mcp"`` returns the canonical surface: pure PREPARE →
  ``commit_proposal``, explicit confirmation, zero ``commit_now``.
- ``projection="gpt_actions"`` maps every capability name through the
  inverse of the canonical parity registry
  (``intelligence.capability_registry``) and injects the Actions-only
  envelope mechanics (``commit_now`` additive contract).

Changing a canonical name/property once rewrites both projections — there
is no second capability list to drift. Unknown neutral names fail closed
(``ProjectionContractError``).
"""

from __future__ import annotations

import copy
from typing import Any

from tm_app.application.governed_writes.confirmation_policy import (
    CONFIRM_BEFORE_ACT,
    execution_policy_for_entity_operation,
    execution_policy_for_workflow,
    confirmation_kind_for_entity_operation,
    confirmation_kind_for_workflow,
)
from tm_app.application.gpt_actions.entities import (
    ENTITY_CAPABILITIES,
    ENTITY_DESCRIPTIONS,
    GptEntity,
)
from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
)
from tm_app.application.intelligence.capability_registry import (
    actions_operation_for_neutral,
    confirmation_policy_label,
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


def _canonical_catalog() -> dict[str, Any]:
    """Single semantic capability surface (transport-neutral names).

    Operation-name fields hold the neutral/MCP names; transport projections
    resolve them through the canonical parity registry.
    """
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
                # Semantic policy — each transport renders its own wording.
                "prepare_act_policy": (
                    "prepare_record_change → commit_proposal"
                    if write_ops
                    else "read_only"
                ),
                "execution_policy": (
                    {
                        op: execution_policy_for_entity_operation(op)
                        for op in write_ops
                    }
                    if write_ops
                    else None
                ),
                "confirmation_policy": (
                    {
                        op: confirmation_kind_for_entity_operation(op)
                        for op in write_ops
                    }
                    if write_ops
                    else None
                ),
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
            "prepare_operation": "prepare_activate_revision",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow("activate_revision"),
            "read_back_policy": "authoritative",
        },
        {
            "id": "improvement_package",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Nested process+instance+revision+measurement package.",
            "read_write": "WRITE",
            "prepare_operation": "prepare_improvement_package",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "improvement_package"
            ),
            "read_back_policy": "authoritative",
        },
        {
            "id": "meeting_minute_workflow",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "send / finalize / cancel meeting minute transitions.",
            "read_write": "WRITE",
            "prepare_operation": "prepare_meeting_minute_workflow",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "meeting_minute_workflow"
            ),
            "read_back_policy": "authoritative",
        },
        {
            "id": "manage_evidence",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Link/metadata evidence (binary upload remains UI-only).",
            "read_write": "WRITE",
            "prepare_operation": "prepare_manage_evidence",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "manage_evidence"
            ),
            "read_back_policy": "authoritative",
        },
        {
            "id": "adjust_shared_resource_cost",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Business cost adjustment for shared resources.",
            "read_write": "WRITE",
            "prepare_operation": "prepare_adjust_shared_resource_cost",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "adjust_shared_resource_cost"
            ),
            "read_back_policy": "authoritative",
        },
        {
            "id": "recalculate_dashboard",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Recalculate materialised dashboard cache.",
            "read_write": "WRITE",
            "prepare_operation": "prepare_recalculate_dashboard",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "recalculate_dashboard"
            ),
            "read_back_policy": "authoritative",
        },
        {
            "id": "meeting_minute_manage",
            "kind": "workflow",
            "owner": "transformometro-api",
            "description": "Meeting-minute extras (reads + governed writes like resend).",
            "read_write": "MIXED",
            "prepare_operation": "prepare_meeting_minute_manage",
            "commit_via": "commit_proposal",
            "confirmation_requirement": True,
            "confirmation_policy": confirmation_kind_for_workflow(
                "meeting_minute_manage"
            ),
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
            "operation": "analyze",
        },
        {
            "id": "methodology_guide",
            "kind": "analysis",
            "owner": "transformometro-api",
            "description": "Method playbooks (not domain facts / AuthZ / writes).",
            "read_only": True,
            "operation": "get_methodology_guide",
        },
        {
            "id": "process_timeline",
            "kind": "analysis",
            "owner": "transformometro-api",
            "description": "Process audit timeline.",
            "read_only": True,
            "operation": "get_process_timeline",
        },
    ]
    # Canonical write-execution policy drives the confirmation flag
    # and is exposed verbatim so transports/agents can branch on it.
    for workflow in workflows:
        policy = execution_policy_for_workflow(workflow["id"])
        workflow["execution_policy"] = policy
        workflow["confirmation_requirement"] = policy == CONFIRM_BEFORE_ACT

    return {
        "surface_version": "teo-capabilities-v3",
        "proposal_model": {
            "prepare_then_commit": True,
            "opaque_proposal_handle": True,
            "commit_operation": "commit_proposal",
            "write_execution_policy": {
                "auto_act": (
                    "non-destructive write executes immediately after "
                    "governed PREPARE; no conversational confirmation"
                ),
                "confirm_before_act": (
                    "destructive/consequential write requires ONE explicit "
                    "user confirmation of the exact prepared change"
                ),
            },
            "ttl_seconds_default": 900,
            "store": "in_process",
            "store_residual": "ACCEPTED_WITH_RESIDUAL for multi-replica",
            "note": (
                "commit_proposal is NOT a generic proxy: it only executes "
                "sealed server-side proposals produced by governed PREPARE. "
                "Material execution occurs only through commit."
            ),
        },
        "rules": {
            "agent_directives_are_live": True,
            "builder_instructions_are_stable_only": True,
        },
        # MCP-native capabilities: discoverable here, but they declare NO
        # actions operation and must not be treated as GPT Actions.
        "mcp_only_capabilities": [
            {
                "id": "diagnostic_v1",
                "kind": "domain_capability",
                "owner": "transformometro-api",
                "surface_availability": {"mcp": True, "gpt_actions": False},
                "mcp": {
                    "read_tools": [
                        "get_diagnostic",
                        "list_diagnostics_by_revision",
                    ],
                    "prepare_tools": [
                        "prepare_create_diagnostic",
                        "prepare_manage_diagnostic",
                    ],
                    "commit_tool": "commit_proposal",
                },
                "manage_actions": [
                    "add_finding",
                    "add_hypothesis",
                    "add_causal_link",
                    "add_evidence_link",
                    "add_conclusion",
                    "validate_hypothesis",
                    "reject_hypothesis",
                    "supersede_hypothesis",
                    "mark_hypothesis_stale_evidence",
                    "mark_hypothesis_revalidation_required",
                    "validate_conclusion",
                    "reject_conclusion",
                    "supersede_conclusion",
                ],
                "confirmation_requirement": True,
                "commit_now": False,
                "server_generated_ids": [
                    "diagnostic_id",
                    "finding_id",
                    "hypothesis_id",
                    "link_id",
                    "conclusion_id",
                ],
                "permission_metadata": {
                    "note": "Catalog is not AuthZ. Backend enforces transformometro.access.",
                    "typical_gate": "transformometro.access",
                },
            }
        ],
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


def _render_confirmation_labels(node: Any, transport: str) -> None:
    """Project semantic confirmation kinds into transport labels in place."""
    for entity in node.get("entities") or []:
        policy = entity.get("confirmation_policy")
        if isinstance(policy, dict):
            for op, kind in policy.items():
                policy[op] = confirmation_policy_label(kind, transport)
        if entity.get("write_operations"):
            if transport == "gpt_actions":
                entity["prepare_act_policy"] = (
                    "prepare_record_change → commit_proposal "
                    "(additive may use commit_now=true)"
                )
            else:
                entity["prepare_act_policy"] = (
                    "prepare_record_change → commit_proposal "
                    "(per-op execution_policy: auto_act | confirm_before_act)"
                )
    for workflow in node.get("workflows") or []:
        kind = workflow.get("confirmation_policy")
        if isinstance(kind, str):
            workflow["confirmation_policy"] = confirmation_policy_label(
                kind, transport
            )


def _project_catalog_for_actions(catalog: dict[str, Any]) -> dict[str, Any]:
    """Derive the Actions wire surface from the canonical neutral model.

    Capability names map through the inverse parity registry (fail closed);
    the Actions-only envelope (``commit_now`` additive contract) exists only
    in this projection — the MCP projection never carries it.
    """
    out = copy.deepcopy(catalog)
    out["surface_version"] = "teo-gpt-actions-v2"
    proposal = out["proposal_model"]
    proposal["commit_operation"] = actions_operation_for_neutral(
        proposal["commit_operation"]
    )
    proposal["commit_now_parameter"] = True
    proposal["note"] = (
        "commit_proposal is NOT a generic proxy: it only executes "
        "server-side proposals produced by governed PREPARE. "
        "Additive prepare may set commit_now=true for atomic PREPARE+ACT."
    )
    for workflow in out.get("workflows") or []:
        for key in ("prepare_operation", "commit_via"):
            name = workflow.get(key)
            if name:
                workflow[key] = actions_operation_for_neutral(name)
    for analysis in out.get("analyses") or []:
        name = analysis.get("operation")
        if name:
            analysis["operation"] = actions_operation_for_neutral(name)
    _render_confirmation_labels(out, "gpt_actions")
    out["agent_directives"] = TeoAgentIntelligenceService.agent_directives(
        transport="gpt_actions"
    )
    return out


def _project_catalog_for_mcp(catalog: dict[str, Any]) -> dict[str, Any]:
    """MCP projection of the canonical surface — pure PREPARE contract."""
    from tm_app.application.intelligence.transport_projection import (
        neutralize_for_mcp,
    )

    out = copy.deepcopy(catalog)
    _render_confirmation_labels(out, "mcp")
    out["agent_directives"] = TeoAgentIntelligenceService.agent_directives(
        transport="mcp"
    )
    # Residual prose neutralization (bounded, fail-closed on unknown names).
    return neutralize_for_mcp(out)


def build_capability_surface_catalog(projection: str = "gpt_actions") -> dict[str, Any]:
    """Project the capability surface for the requested transport.

    ``projection="gpt_actions"`` (default) preserves the Actions contract:
    ``gpt_*`` operation names + additive ``commit_now`` policy.
    ``projection="mcp"`` serves MCP-callable names only — ``prepare_*`` /
    ``commit_proposal``, explicit confirmation, zero ``commit_now``.
    """
    catalog = _canonical_catalog()
    if projection == "mcp":
        return _project_catalog_for_mcp(catalog)
    return _project_catalog_for_actions(catalog)
