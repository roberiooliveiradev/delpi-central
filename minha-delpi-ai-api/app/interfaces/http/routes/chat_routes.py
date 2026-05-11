from dataclasses import asdict

from flask import Blueprint, g, jsonify, request

from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.application.use_cases.get_chat_status_use_case import GetChatStatusUseCase
from app.composition.chat_composer import (
    make_create_chat_session_use_case,
    make_get_chat_history_use_case,
    make_list_chat_sessions_use_case,
)
from app.extensions.db import db
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.utils.errors import bad_request

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.get("/status")
@require_permission("minha-delpi.chat.access")
def status():
    result = GetChatStatusUseCase().execute(g.current_user)
    return jsonify(result), 200


@chat_bp.post("/sessions")
@require_permission("minha-delpi.chat.access")
def create_session():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_session_use_case()

    result = use_case.execute(
        CreateChatSessionRequest(
            user_id=g.current_user.sub,
            title=payload.get("title"),
            context=payload.get("context"),
        )
    )

    db.session.commit()

    return jsonify(asdict(result)), 201


@chat_bp.get("/sessions")
@require_permission("minha-delpi.chat.access")
def list_sessions():
    use_case = make_list_chat_sessions_use_case()
    result = use_case.execute(g.current_user.sub)

    return jsonify([asdict(session) for session in result]), 200


@chat_bp.get("/sessions/<session_id>/messages")
@require_permission("minha-delpi.chat.access")
def get_history(session_id: str):
    use_case = make_get_chat_history_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(message) for message in result]), 200
