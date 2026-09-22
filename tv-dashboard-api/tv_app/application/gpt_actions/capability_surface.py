"""Capability surface descriptors for VISTA GPT catalog projection.

Catalog informs; backend authorizes. Descriptors are not AuthZ authority.
Typed presentation ops remain owned by ``presentation_ops_content.json``
(PresentationMutation / TvPresentationPatchV1).
"""

from __future__ import annotations

from typing import Any

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService


def build_capability_surface() -> dict[str, Any]:
    """Project Action-facing capability taxonomy without a second domain catalog."""
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
                    "Playlist presentation aggregate (slides, sections, revision). "
                    "Read via dedicated Actions; writes only through governed workflow."
                ),
                "read_operations": [
                    "gpt_list_playlists",
                    "gpt_get_playlist_context",
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
                    "topo-sort + as/*Ref; preview mints opaque proposal; additive "
                    "commit_now; commit → TvPresentationWriteService + read-back."
                ),
                "read_operations": ["gpt_get_catalog", "gpt_get_playlist_context"],
                "write_operations": [
                    "gpt_suggest_change",
                    "gpt_preview_change",
                    "gpt_commit_change",
                ],
                "typed_ops_authority": "presentation_ops_content.json",
                "mutation_engine": "presentation_mutation.PresentationPatchService",
                "typed_ops_count": len(ops),
                "destructive_typed_ops": destructive,
                "prepare_act_policy": {
                    "prepare": "gpt_preview_change",
                    "suggest": "gpt_suggest_change",
                    "commit": "gpt_commit_change",
                    "commit_input": ["proposal_handle", "confirmation"],
                    "additive_single_shot": {
                        "operation": "gpt_preview_change",
                        "commit_now": True,
                        "when": "confirmationPolicy=direct",
                    },
                    "opaque_proposal": True,
                    "compound_plan": True,
                    "plan_compiler": "topo_sort",
                },
                "confirmation_policy": {
                    "always_require_confirmed_true": True,
                    "destructive_ops_policy": "confirm",
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
                "read_operations": ["gpt_search_data_routes"],
                "write_operations": [],
                "confirmation_policy": None,
                "prepare_act_policy": None,
                "required_permission_metadata": {"read": "tv-dashboard.read"},
            },
            {
                "id": "data_block_preview",
                "kind": "ANALYSIS",
                "owner": "tv-dashboard-api",
                "description": (
                    "Preview data block resolution without persisting. Read-only."
                ),
                "read_operations": ["gpt_preview_data_block"],
                "write_operations": [],
                "confirmation_policy": None,
                "prepare_act_policy": None,
                "required_permission_metadata": {"read": "tv-dashboard.read"},
            },
        ],
        "rules": {
            "catalog_is_not_authz": True,
            "new_typed_op_does_not_add_action": True,
            "no_generic_http_or_sql_proxy": True,
            "proposal_store": "in_process_accept_with_residual",
        },
    }
