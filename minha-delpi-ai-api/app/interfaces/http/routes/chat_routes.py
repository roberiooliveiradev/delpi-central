from flask import Blueprint, g, jsonify

from app.application.use_cases.get_chat_status_use_case import GetChatStatusUseCase
from app.interfaces.http.auth_decorators import require_permission

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.get("/status")
@require_permission("minha-delpi.chat.access")
def status():
    result = GetChatStatusUseCase().execute(g.current_user)
    return jsonify(result), 200
