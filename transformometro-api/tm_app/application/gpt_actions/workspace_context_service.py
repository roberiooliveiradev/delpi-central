"""TÉO-facing projection of the user's current Transformômetro workspace.

Answers "which process/instance/revision/section is the user looking at
right now" for deictic references ("este processo", "a revisão aberta").
It resolves bounded entity refs from the canonical WorkspaceContext
contract — never domain facts, never authorization. Callers must follow
with ``get_process_context`` for the authoritative read.
"""

from __future__ import annotations

from typing import Any, Mapping

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.infrastructure.gateways.core_workspace_context_gateway import (
    CoreWorkspaceContextGateway,
)

_STATUS_VALUES = ("active", "absent", "stale", "ambiguous")

_NOT_DOMAIN_NOTE = (
    "Workspace navigation hint — NOT domain truth, NOT authorization. "
    "Follow with get_process_context for authoritative state."
)


def _refs_by_type(entity_refs: Any) -> dict[str, str]:
    refs: dict[str, str] = {}
    if not isinstance(entity_refs, list):
        return refs
    for ref in entity_refs:
        if not isinstance(ref, Mapping):
            continue
        entity_type = ref.get("entity_type")
        entity_id = ref.get("entity_id")
        if entity_type and entity_id and entity_type not in refs:
            refs[str(entity_type)] = str(entity_id)
    return refs


def _project_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    context = context or {}
    refs = _refs_by_type(context.get("entity_refs"))
    presentation = context.get("presentation_state") or {}
    return {
        "app_id": context.get("app_id"),
        "route_id": context.get("route_id"),
        "process_id": refs.get("process"),
        "instance_id": refs.get("instance"),
        "revision_id": refs.get("revision"),
        "area": presentation.get("area") if isinstance(presentation, Mapping) else None,
        "canonical_path": context.get("canonical_path"),
        "updated_at": context.get("updated_at"),
        "age_seconds": context.get("age_seconds"),
    }


class WorkspaceContextService:
    def __init__(self, gateway: CoreWorkspaceContextGateway | None = None) -> None:
        self._gateway = gateway or CoreWorkspaceContextGateway()

    def get_workspace_context(self, authorization: str) -> dict[str, Any]:
        authorization = str(authorization or "").strip()
        if not authorization:
            raise GptActionsError(
                "Usuário não autenticado.",
                401,
                {"error_kind": "authn"},
            )

        resolved = self._gateway.get_my_workspace_context(authorization)
        status = str(resolved.get("status") or "absent")
        if status not in _STATUS_VALUES:
            status = "absent"

        payload: dict[str, Any] = {
            "status": status,
            "context_version": "workspace_context_v1",
            "note": _NOT_DOMAIN_NOTE,
        }
        if status in ("active", "stale"):
            payload.update(_project_context(resolved.get("context")))
        if status == "active":
            payload["next_step"] = (
                "Use the entity refs (process_id/instance_id/revision_id) with "
                "get_process_context for the authoritative domain read."
            )
        elif status == "ambiguous":
            candidates = resolved.get("candidates") or []
            payload["candidates"] = [_project_context(c) for c in candidates[:4]]
            payload["next_step"] = (
                "Ask one discriminating question naming the candidate process "
                "or section before reading domain data."
            )
        elif status == "stale":
            payload["next_step"] = (
                "Workspace context is stale — ask the user to confirm the "
                "process or refresh the Portal."
            )
        else:
            payload["next_step"] = (
                "No current workspace. Ask the user for the process — never "
                "guess by recency or silent search."
            )
        return payload
