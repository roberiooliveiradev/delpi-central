import json
from dataclasses import asdict

from flask import Blueprint, Response, g, jsonify, request, stream_with_context

from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.get_chat_status_use_case import GetChatStatusUseCase
from app.composition.chat_composer import (
    make_create_chat_session_use_case,
    make_get_chat_history_use_case,
    make_list_chat_sessions_use_case,
    make_send_chat_message_use_case,
    make_stream_chat_message_use_case,
)
from app.extensions.db import db
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.utils.errors import bad_request

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


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

    try:
        result = use_case.execute(
            CreateChatSessionRequest(
                user_id=g.current_user.sub,
                title=payload.get("title"),
                context=payload.get("context"),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

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


@chat_bp.post("/sessions/<session_id>/messages")
@require_permission("minha-delpi.chat.ask")
def send_message(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_send_chat_message_use_case()

    try:
        result = use_case.execute(
            SendChatMessageRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                message=payload.get("message", ""),
                context=payload.get("context"),
                access_token=g.access_token,
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.post("/sessions/<session_id>/messages/stream")
@require_permission("minha-delpi.chat.ask")
def stream_message(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    request_dto = SendChatMessageRequest(
        user_id=g.current_user.sub,
        session_id=session_id,
        message=payload.get("message", ""),
        context=payload.get("context"),
        access_token=g.access_token,
    )

    use_case = make_stream_chat_message_use_case()

    @stream_with_context
    def generate():
        try:
            for event in use_case.stream(request_dto):
                event_type = event.get("type", "message")

                if event_type == "sources":
                    yield _sse("sources", {"sources": event.get("sources", [])})

                elif event_type == "tool_calls":
                    yield _sse("tool_calls", {"toolCalls": event.get("toolCalls", [])})

                elif event_type == "token":
                    yield _sse("token", {"content": event.get("content", "")})

                elif event_type == "done":
                    db.session.commit()
                    yield _sse(
                        "done",
                        {
                            "messageId": event.get("messageId"),
                            "answer": event.get("answer", ""),
                            "sources": event.get("sources", []),
                            "toolCalls": event.get("toolCalls", []),
                        },
                    )

            yield _sse("close", {"ok": True})

        except GeneratorExit:
            db.session.rollback()
            raise

        except Exception as exc:
            db.session.rollback()
            yield _sse(
                "error",
                {
                    "message": getattr(exc, "message", "Erro ao gerar resposta em streaming."),
                },
            )

    response = Response(
        generate(),
        mimetype="text/event-stream",
    )

    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"

    return response
