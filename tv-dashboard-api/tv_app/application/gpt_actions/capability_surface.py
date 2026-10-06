"""Capability surface descriptors — transport-neutral canonical model.

Catalog informs; backend authorizes. Descriptors are not AuthZ authority.
Typed presentation ops remain owned by ``presentation_ops_content.json``
(PresentationMutation / TvPresentationPatchV1).

Mutable specialist intelligence (object resolution, modes, write heuristics)
lives in ``vista_agent_intelligence.json`` and is projected as
``agent_directives`` so it ships with API deploy — not GPT Builder paste.

Architecture: ONE canonical semantic surface uses transport-neutral capability
names (the MCP tool names — they carry no transport prefix). Each transport
gets a derived projection:

- ``transport="mcp"`` returns the canonical surface unchanged.
- ``transport="actions"`` maps every capability name through the inverse of
  the canonical ``surface_parity.parity_map`` registry and injects the
  Actions-only envelope mechanics (``commit_now`` / ``additive_single_shot``).

Changing a canonical name/property once rewrites both projections — there is
no second capability list to drift.
"""

from __future__ import annotations

import copy
from typing import Any

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
)
from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService
from tv_app.application.services.data.value_expression_service import (
    expression_capability,
)


def _parity_map() -> dict[str, str]:
    """Canonical Actions→neutral transport registry (vista_agent_intelligence)."""
    doc = VistaAgentIntelligenceService.document()
    parity = doc.get("surface_parity") or {}
    mapping = parity.get("parity_map") or {}
    return {
        str(k): str(v) for k, v in mapping.items() if isinstance(k, str) and isinstance(v, str)
    }


def _neutral_to_actions() -> dict[str, str]:
    """Inverse of the canonical parity map: neutral name → Actions op id."""
    return {neutral: actions for actions, neutral in _parity_map().items()}


def _actions_ops(names: list[str]) -> list[str]:
    mapping = _neutral_to_actions()
    return [mapping.get(name, name) for name in names]


def _canonical_surface() -> dict[str, Any]:
    """Single semantic capability surface (transport-neutral names)."""
    ops = PresentationOpsContentService.operations()
    destructive = sorted(
        name
        for name, spec in ops.items()
        if isinstance(spec, dict)
        and str(spec.get("confirmationPolicy") or "").strip().lower() == "confirm"
    )
    return {
        "lifecycle": "GOVERNED_PREPARE_COMMIT_V2",
        "mutation_owner": "PresentationMutation",
        "action_surface_budget": {
            "importable_operations": len(GPT_ACTIONS_OPERATION_IDS),
            "platform_prefer_max": 30,
            "new_crud_entity_adds_actions": 0,
        },
        "entities": [
            {
                "id": "playlist",
                "kind": "ENTITY",
                "owner": "tv-dashboard-api",
                "description": (
                    "Playlist aggregate (slides, sections, revision). "
                    "Writes only via governed workflow."
                ),
                "read_operations": [
                    "list_playlists",
                    "get_playlist_context",
                ],
                "write_operations": [],
                "filterable_fields": [],
                "sortable_fields": [],
                "server_owned_fields": ["id", "revision", "ownerUserId", "publicToken"],
                "required_permission_metadata": {
                    "read": "tv-dashboard.read",
                    "write": "tv-dashboard.write",
                    "resource": "PlaylistAccessService",
                },
                "confirmation_policy": None,
                "prepare_act_policy": None,
                "read_back_policy": None,
            }
        ],
        "workflows": [
            {
                "id": "presentation_change",
                "kind": "WORKFLOW",
                "owner": "tv-dashboard-api",
                "description": (
                    "Governed PresentationMutation compound change: PlanCompiler "
                    "topo-sort + as/*Ref; PREPARE mints opaque proposal; ACT → "
                    "TvPresentationWriteService + read-back."
                ),
                "read_operations": ["get_catalog", "get_playlist_context"],
                "write_operations": [
                    "suggest_change",
                    "prepare_change",
                    "commit_proposal",
                ],
                "typed_ops_authority": "presentation_ops_content.json",
                "mutation_engine": "presentation_mutation.PresentationPatchService",
                "typed_ops_count": len(ops),
                "destructive_typed_ops": destructive,
                "prepare_act_policy": {
                    "suggest": "suggest_change",
                    "prepare": "prepare_change",
                    "commit": "commit_proposal",
                    "commit_input": ["proposal_handle", "confirmation", "idempotency_key"],
                    "opaque_proposal": True,
                    "compound_plan": True,
                    "plan_compiler": "topo_sort",
                },
                "confirmation_policy": {
                    "scoped_per_operation": True,
                    "destructive_ops_policy": "confirm",
                    "non_destructive_ops_policy": "direct",
                },
                "read_back_policy": "authoritative_after_commit",
                "required_permission_metadata": {
                    "prepare": "tv-dashboard.write",
                    "commit": "tv-dashboard.write",
                    "resource_edit": "PlaylistAccessService.can_edit",
                },
            }
        ],
        "analyses": [
            {
                "id": "data_route_search",
                "kind": "ANALYSIS",
                "owner": "tv-dashboard-api",
                "description": "Search allowlisted TV data routes. Read-only.",
                "read_operations": ["search_data_routes"],
                "write_operations": [],
                "required_permission_metadata": {"read": "tv-dashboard.read"},
            },
            {
                "id": "data_block_preview",
                "kind": "ANALYSIS",
                "owner": "tv-dashboard-api",
                "description": (
                    "Preview data block resolution without persisting. Read-only."
                ),
                "read_operations": ["preview_data_block"],
                "write_operations": [],
                "required_permission_metadata": {"read": "tv-dashboard.read"},
            },
            {
                "id": "domain_intent_materialization",
                "kind": "ANALYSIS",
                "owner": "tv-dashboard-api",
                "description": "NL intent → typed ops + clarification. Never persists; never authorizes.",
                "read_operations": ["suggest_change"],
                "write_operations": [],
                "required_permission_metadata": {"read": "tv-dashboard.write"},
            },
            {
                "id": "data_model_lifecycle",
                "kind": "ANALYSIS",
                "owner": "tv-dashboard-api",
                "description": (
                    "DataModel = logical data unit (1..N embedded inputs + "
                    "transform, non-visual). Preview/inspect read-only; "
                    "upsert/delete/migrate via governed typed ops."
                ),
                "read_operations": [
                    "preview_data_model",
                    "inspect_data_model",
                ],
                "write_operations": [
                    "upsert_data_model",
                    "patch_data_model",
                    "delete_data_model",
                    "migrate_data_sources_to_model",
                    "bind_visual",
                ],
                "required_permission_metadata": {"read": "tv-dashboard.read"},
            },
        ],
        "rules": {
            "catalog_is_not_authz": True,
            "new_typed_op_does_not_add_action": True,
            "no_generic_http_or_sql_proxy": True,
            "proposal_store": "in_process_accept_with_residual",
            "agent_directives_are_live": True,
            "builder_instructions_are_stable_only": True,
        },
    }


def _project_for_actions(surface: dict[str, Any]) -> dict[str, Any]:
    """Derive the Actions wire surface from the canonical neutral model.

    Capability names map through the inverse parity map; the Actions-only
    envelope mechanics (``commit_now`` single-shot) exist only here — the MCP
    projection never carries them.
    """
    projected = copy.deepcopy(surface)
    for entity in projected.get("entities") or []:
        for key in ("read_operations", "write_operations"):
            if isinstance(entity.get(key), list):
                entity[key] = _actions_ops(entity[key])
    for workflow in projected.get("workflows") or []:
        for key in ("read_operations", "write_operations"):
            if isinstance(workflow.get(key), list):
                workflow[key] = _actions_ops(workflow[key])
        policy = workflow.get("prepare_act_policy")
        if isinstance(policy, dict):
            for key in ("suggest", "prepare", "commit"):
                name = policy.get(key)
                if isinstance(name, str):
                    policy[key] = _neutral_to_actions().get(name, name)
            # Actions envelope single-shot: PREPARE may commit inline when the
            # confirmation policy is direct — an adapter-level mechanic that
            # must never appear in the MCP projection.
            policy["additive_single_shot"] = {
                "operation": _neutral_to_actions().get("prepare_change", "prepare_change"),
                "commit_now": True,
                "when": "confirmationPolicy=direct",
            }
    for analysis in projected.get("analyses") or []:
        for key in ("read_operations", "write_operations"):
            if isinstance(analysis.get(key), list):
                analysis[key] = _actions_ops(analysis[key])
    return projected


def build_capability_surface(*, transport: str = "actions") -> dict[str, Any]:
    """Project the capability taxonomy for the requested transport.

    The canonical model is transport-neutral; each transport receives a
    derived projection so a single semantic change propagates to both.
    """
    surface = _canonical_surface()
    surface["agent_directives"] = VistaAgentIntelligenceService.agent_directives(
        transport=transport
    )
    surface["designIntelligence"] = DesignIntelligenceService.catalog_projection()
    surface["expressions"] = expression_capability(transport=transport)
    if transport == "actions":
        return _project_for_actions(surface)
    # Actions-envelope budget metadata is adapter semantics — never on MCP.
    surface.pop("action_surface_budget", None)
    return surface
