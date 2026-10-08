# app/interfaces/http/workspace_context_controller.py
"""Current workspace context — per-user ephemeral navigation hints.

Publishers (MFEs) report where the user's screen is; conversational
surfaces (TÉO, DÉLIA) resolve it. This channel never grants authorization
and never carries domain state — only bounded entity refs.
"""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request

from app.application.workspace_context.workspace_context_contract import (
    WorkspaceContextValidationError,
    parse_workspace_context_payload,
)
from app.application.workspace_context.workspace_context_service import (
    WorkspaceContextService,
)
from app.interfaces.http.security.authorization import require_auth
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

workspace_context_bp = Blueprint("workspace_context", __name__)


def _user_id() -> str:
    return str(g.current_user.id)


@workspace_context_bp.route("/me/workspace-context", methods=["PUT"])
@require_auth()
def publish_workspace_context():
    try:
        payload = parse_workspace_context_payload(request.get_json(silent=True))
    except WorkspaceContextValidationError as exc:
        return api_error("workspace_context_invalid", str(exc), status=400)

    result = WorkspaceContextService().publish(user_id=_user_id(), payload=payload)
    return jsonify(result), 200


@workspace_context_bp.route("/me/workspace-context", methods=["GET"])
@require_auth()
def resolve_workspace_context():
    app_id = request.args.get("app_id") or None
    result = WorkspaceContextService().resolve(user_id=_user_id(), app_id=app_id)
    return jsonify(result), 200


@workspace_context_bp.route("/me/workspace-context", methods=["DELETE"])
@require_auth()
def delete_workspace_context():
    client_instance_id = request.args.get("client_instance_id") or None
    if not client_instance_id:
        return api_error(
            "workspace_context_invalid", "client_instance_id is required", status=400
        )
    result = WorkspaceContextService().unpublish(
        user_id=_user_id(), client_instance_id=client_instance_id
    )
    return jsonify(result), 200
