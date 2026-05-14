from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
from dataclasses import asdict

from flask import Blueprint, g, jsonify, request

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.composition.tool_composer import make_execute_tool_use_case
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.rate_limit_decorators import rate_limit
from app.interfaces.http.utils.errors import bad_request

tool_bp = Blueprint("tools", __name__, url_prefix="/tools")


@tool_bp.post("/execute")
@require_permission(CHAT_TOOLS_USE_PERMISSION)
@rate_limit("tool_calls", Settings.RATE_LIMIT_TOOL_CALLS_PER_WINDOW)
def execute_tool():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    tool_name = str(payload.get("tool") or "").strip()
    arguments = payload.get("arguments") or {}

    if not tool_name:
        return bad_request("tool is required")

    if not isinstance(arguments, dict):
        return bad_request("arguments must be an object")

    use_case = make_execute_tool_use_case()

    try:
        result = use_case.execute(
            ExecuteToolRequest(
                user_id=g.current_user.sub,
                access_token=g.access_token,
                tool_name=tool_name,
                arguments=arguments,
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200
