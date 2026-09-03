from __future__ import annotations

from typing import Any

from requests_app.core.serialize import json_safe
from requests_app.domain.entities import Request, RequestType
from requests_app.domain.services.workflow_engine import WorkflowEngine


def serialize_request_type(request_type: RequestType) -> dict[str, Any]:
    workflow = request_type.workflow_definition or {}
    return json_safe(
        {
            "id": request_type.id,
            "code": request_type.code,
            "name": request_type.name,
            "description": request_type.description,
            "category": request_type.category,
            "icon": request_type.icon,
            "active": request_type.active,
            "version": request_type.version,
            "presentation_mode": request_type.presentation_mode,
            "branch_scope": request_type.branch_scope,
            "form_schema": request_type.form_schema,
            "ui_schema": request_type.ui_schema,
            "workflow_definition": workflow,
            "destination_config": request_type.destination_config,
            "permission_prefix": request_type.permission_prefix,
            "capabilities": list(
                (request_type.destination_config or {}).get("capabilities") or []
            ),
        }
    )


def serialize_request(
    request: Request,
    *,
    allowed_actions: list[str] | None = None,
    workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    aliases = (workflow or {}).get("statusAliases") or {}
    alias = aliases.get(request.status)
    payload = {
        "id": request.id,
        "request_number": request.request_number,
        "type_code": request.type_code,
        "status": request.status,
        "status_alias": alias,
        "priority": request.priority,
        "branch_code": request.branch_code,
        "payload": request.payload,
        "return_reason": request.return_reason,
        "cancel_justification": request.cancel_justification,
        "version": request.version,
        "created_by_user_id": request.created_by_user_id,
        "created_by_name": request.created_by_name,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "completed_at": request.completed_at,
        "cancelled_at": request.cancelled_at,
        "allowed_actions": allowed_actions or [],
    }
    return json_safe(payload)


def allowed_actions_for(
    request: Request,
    *,
    actor,
    workflow: dict[str, Any],
    engine: WorkflowEngine | None = None,
) -> list[str]:
    engine = engine or WorkflowEngine()
    return engine.compute_allowed_actions(
        request=request,
        actor=actor,
        workflow=workflow,
    )
