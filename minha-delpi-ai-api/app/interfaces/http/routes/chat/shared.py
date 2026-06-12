"""Blueprint e helpers compartilhados das rotas de chat."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from flask import Blueprint, Response, current_app, g, jsonify, request, stream_with_context

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.security.chat_permissions import (
    CHAT_ADMIN_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
)
from app.composition.chat_composer import (
    make_list_chat_agent_action_providers_use_case,
    make_stream_chat_message_use_case,
)
from app.composition.repository_composer import make_chat_agent_repository
from app.infrastructure.gateways.core_me_gateway import CoreMeGateway
from app.interfaces.http.services.chat_sse_stream_service import (
    stream_chat_events_with_background_completion,
)


logger = logging.getLogger("minha-delpi-ai-api.chat")

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _parse_optional_bool(payload: dict, *keys: str) -> bool | None:
    for key in keys:
        if key not in payload:
            continue

        value = payload.get(key)

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {"true", "1", "yes", "sim"}:
                return True

            if normalized in {"false", "0", "no", "nao", "não"}:
                return False

        return bool(value)

    return None


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _typing_correction_enabled() -> bool:
    from app.application.services.chat_platform_runtime_access import (
        learning_pipeline_settings,
    )

    learning = learning_pipeline_settings()
    return bool(learning.get("learningEnabled") and learning.get("typingCorrectionEnabled"))


def _get_chat_capabilities_from_request() -> dict:
    authorization_header = request.headers.get("Authorization")
    core_user = CoreMeGateway().get_me(authorization_header)

    user = g.current_user
    permissions = set()
    is_superadmin = False

    if core_user:
        permissions = set(core_user.get("permissions") or [])
        is_superadmin = bool(core_user.get("is_superadmin"))
    else:
        permissions = set(getattr(user, "permissions", []) or [])
        is_superadmin = bool(getattr(user, "is_superadmin", False))

    can_manage_own_agents = (
        is_superadmin
        or CHAT_TOOLS_MANAGE_PERMISSION in permissions
        or CHAT_ADMIN_PERMISSION in permissions
    )
    can_manage_official_agents = (
        is_superadmin
        or CHAT_ADMIN_PERMISSION in permissions
    )
    can_manage_tools = can_manage_own_agents
    can_open_admin = (
        is_superadmin
        or CHAT_ADMIN_PERMISSION in permissions
        or CHAT_KNOWLEDGE_MANAGE_PERMISSION in permissions
        or CHAT_TOOLS_MANAGE_PERMISSION in permissions
    )

    from app.infrastructure.config.settings import Settings

    return {
        "permissions": sorted(permissions),
        "isSuperadmin": is_superadmin,
        "canOpenAdmin": can_open_admin,
        "canManageAgents": can_manage_own_agents,
        "canManageOwnAgents": can_manage_own_agents,
        "canManageOfficialAgents": can_manage_official_agents,
        "canManageTools": can_manage_tools,
        "canUseTools": (
            can_manage_tools
            or CHAT_TOOLS_MANAGE_PERMISSION in permissions
        ),
        "typingCorrectionEnabled": _typing_correction_enabled(),
        "knowledgeDocumentMaxChars": Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS,
    }


def _can_manage_agent_configuration(agent_id: str) -> tuple[bool, dict]:
    capabilities = _get_chat_capabilities_from_request()

    if not capabilities["canManageAgents"]:
        return False, capabilities

    try:
        agent_uuid = UUID(agent_id)
        user_uuid = UUID(g.current_user.sub)
    except ValueError:
        return False, capabilities

    record = make_chat_agent_repository().get_accessible_by_id(
        agent_uuid,
        user_uuid,
    )

    if not record:
        return False, capabilities

    agent, access_role = record
    is_official_agent = (
        agent.visibility == "system"
        or agent.owner_user_id is None
        or access_role == "system"
    )

    if is_official_agent:
        return bool(capabilities["canManageOfficialAgents"]), capabilities

    return access_role in {"owner", "editor"}, capabilities


def _parse_response_mode(payload: dict) -> str | None:
    raw = payload.get("responseMode")

    if raw is None:
        raw = payload.get("response_mode")

    if raw is None:
        return None

    return str(raw).strip() or None


def _parse_response_format(payload: dict) -> str | None:
    raw = payload.get("responseFormat")

    if raw is None:
        raw = payload.get("response_format")

    if raw is None:
        return None

    token = str(raw).strip().lower()

    if token in {"", "auto"}:
        return None

    if token in {"table", "text", "tree", "chart", "canvas", "topics", "dashboard"}:
        return token

    return None


def _can_use_admin_debug() -> bool:
    authorization_header = request.headers.get("Authorization")
    core_user = CoreMeGateway().get_me(authorization_header)

    if core_user:
        if bool(core_user.get("is_superadmin")):
            return True

        permissions = set(core_user.get("permissions") or [])
        return bool(
            CHAT_ADMIN_PERMISSION in permissions
            or CHAT_TOOLS_MANAGE_PERMISSION in permissions
            or CHAT_KNOWLEDGE_MANAGE_PERMISSION in permissions
        )

    user = getattr(g, "current_user", None)

    if not user:
        return False

    if bool(getattr(user, "is_superadmin", False)):
        return True

    permissions = set(getattr(user, "permissions", []) or [])

    return bool(
        CHAT_ADMIN_PERMISSION in permissions
        or CHAT_TOOLS_MANAGE_PERMISSION in permissions
        or CHAT_KNOWLEDGE_MANAGE_PERMISSION in permissions
    )


def _normalize_context_id_list(raw) -> list[str] | None:
    if raw is None:
        return None

    if not isinstance(raw, list):
        return None

    seen: set[str] = set()
    normalized: list[str] = []

    for item in raw:
        value = str(item or "").strip()

        if not value or value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized


def _resolve_context_ids_from_payload(
    payload: dict,
    *,
    plural_keys: tuple[str, ...],
    singular_keys: tuple[str, ...],
) -> tuple[str | None, list[str] | None]:
    id_list = None

    for key in plural_keys:
        if key in payload:
            id_list = _normalize_context_id_list(payload.get(key))
            break

    singular = None

    for key in singular_keys:
        if key in payload:
            raw = payload.get(key)
            singular = str(raw).strip() if raw is not None else None
            break

    if id_list is None and singular:
        id_list = [singular]

    primary = (id_list[0] if id_list else None) or singular or None

    return primary, id_list


def _build_send_chat_message_request(
    *,
    session_id: str,
    payload: dict,
    resend_from_message_id: str | None = None,
) -> SendChatMessageRequest:
    message = payload.get("message", "")

    if resend_from_message_id is not None:
        message = payload.get("content", message)

    agent_id, agent_ids = _resolve_context_ids_from_payload(
        payload,
        plural_keys=("agentIds", "agent_ids"),
        singular_keys=("agentId", "agent_id"),
    )
    project_id, project_ids = _resolve_context_ids_from_payload(
        payload,
        plural_keys=("projectIds", "project_ids"),
        singular_keys=("projectId", "project_id"),
    )

    return SendChatMessageRequest(
        user_id=g.current_user.sub,
        session_id=session_id,
        message=message,
        context=payload.get("context"),
        access_token=g.access_token,
        attachment_ids=payload.get("attachmentIds") or payload.get("attachment_ids"),
        agent_id=agent_id,
        agent_ids=agent_ids,
        project_id=project_id,
        project_ids=project_ids,
        sync_project_binding=any(
            key in payload
            for key in ("projectId", "project_id", "projectIds", "project_ids")
        ),
        chat_mode=payload.get("chatMode") or payload.get("chat_mode") or None,
        resend_from_message_id=resend_from_message_id,
        response_mode=_parse_response_mode(payload),
        response_format=_parse_response_format(payload),
        admin_debug=_can_use_admin_debug(),
        typing_correction=_parse_typing_correction(payload),
    )


def _parse_typing_correction(payload: dict) -> dict | None:
    raw = payload.get("typingCorrection") or payload.get("typing_correction")

    if not isinstance(raw, dict):
        return None

    original = str(raw.get("original") or "").strip()
    corrected = str(raw.get("corrected") or raw.get("suggested") or "").strip()
    accepted = raw.get("accepted")

    if not original or not corrected or original == corrected:
        return None

    changes = raw.get("changes")
    safe_changes = changes if isinstance(changes, list) else []

    return {
        "original": original,
        "corrected": corrected,
        "accepted": bool(accepted),
        "source": str(raw.get("source") or "domain_dictionary"),
        "changes": safe_changes,
    }


def _find_linked_agent_provider(agent_id: str, provider_key: str):
    use_case = make_list_chat_agent_action_providers_use_case()
    providers = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    return next(
        (
            item for item in providers
            if item.get("providerKey") == provider_key
        ),
        None,
    )


def _create_source_from_request(use_case, *, user_id: str, owner_id_name: str, owner_id: str):
    if request.files.get("file"):
        file = request.files["file"]
        content = file.read()

        return use_case.execute_file(
            user_id=user_id,
            **{owner_id_name: owner_id},
            original_filename=file.filename or "arquivo",
            content_type=file.content_type,
            content=content,
        )

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")

    return use_case.execute_text(
        user_id=user_id,
        **{owner_id_name: owner_id},
        title=payload.get("title") or "Fonte sem título",
        content=payload.get("content") or "",
        metadata=payload.get("metadata"),
    )


def chat_forbidden(message: str = "Forbidden"):
    return jsonify(
        {
            "errors": [
                {
                    "code": "forbidden",
                    "message": message,
                    "path": "_global",
                }
            ]
        }
    ), 403


def _not_found_response():
    return jsonify(
        {
            "errors": [
                {
                    "code": "not_found",
                    "message": "Resource not found",
                    "path": "_global",
                }
            ]
        }
    ), 404


def _stream_chat_response(session_id: str, request_dto: SendChatMessageRequest):
    use_case = make_stream_chat_message_use_case()
    app = current_app._get_current_object()

    @stream_with_context
    def generate():
        try:
            yield ": connected\n\n"

            for event in stream_chat_events_with_background_completion(
                app,
                lambda: use_case.stream(request_dto),
                session_id=session_id,
            ):
                event_type = event.get("type", "message")

                if event_type == "status":
                    yield _sse(
                        "status",
                        {"message": event.get("message", "")},
                    )
                    yield ": \n\n"

                elif event_type == "activity":
                    yield _sse(
                        "activity",
                        {"entry": event.get("entry", {})},
                    )
                    yield ": \n\n"

                elif event_type == "sources":
                    yield _sse("sources", {"sources": event.get("sources", [])})

                elif event_type == "tool_calls":
                    yield _sse("tool_calls", {"toolCalls": event.get("toolCalls", [])})

                elif event_type == "token":
                    yield _sse("token", {"content": event.get("content", "")})

                elif event_type == "user_persisted":
                    yield _sse(
                        "user_persisted",
                        {"messageId": event.get("messageId")},
                    )

                elif event_type == "session_renamed":
                    yield _sse(
                        "session_renamed",
                        {"title": event.get("title", "")},
                    )

                elif event_type == "assistant_pending":
                    yield _sse(
                        "assistant_pending",
                        {"messageId": event.get("messageId")},
                    )

                elif event_type == "playback":
                    yield _sse(
                        "playback",
                        {
                            "messageId": event.get("messageId"),
                            "answer": event.get("answer", ""),
                            "sources": event.get("sources", []),
                            "toolCalls": event.get("toolCalls", []),
                            "adminDebug": event.get("adminDebug"),
                        },
                    )

                elif event_type == "canvas_open":
                    yield _sse(
                        "canvas_open",
                        {
                            "title": event.get("title", ""),
                            "markdown": event.get("markdown", ""),
                            "sourceMessageId": event.get("sourceMessageId"),
                            "messageId": event.get("messageId"),
                        },
                    )

                elif event_type == "error":
                    yield _sse(
                        "error",
                        {
                            "message": event.get(
                                "message",
                                "Erro ao gerar resposta em streaming.",
                            ),
                            "detail": event.get("detail", ""),
                            "errorType": event.get("errorType", "StreamError"),
                        },
                    )

                elif event_type == "done":
                    done_payload = {
                        "messageId": event.get("messageId"),
                        "answer": event.get("answer", ""),
                        "sources": event.get("sources", []),
                        "toolCalls": event.get("toolCalls", []),
                        "playback": event.get("playback"),
                        "adminDebug": event.get("adminDebug"),
                    }

                    if event.get("canvasOpen"):
                        done_payload["canvasOpen"] = event.get("canvasOpen")

                    yield _sse("done", done_payload)

            yield _sse("close", {"ok": True})

        except GeneratorExit:
            logger.info(
                "chat_stream_client_disconnected",
                extra={
                    "session_id": session_id,
                    "user_id": getattr(g.current_user, "sub", None),
                },
            )
            raise

        except Exception as exc:
            logger.exception(
                "chat_stream_failed",
                extra={
                    "session_id": session_id,
                    "user_id": getattr(g.current_user, "sub", None),
                    "error_type": exc.__class__.__name__,
                },
            )
            detail = getattr(exc, "message", None) or str(exc) or "Erro desconhecido."

            yield _sse(
                "error",
                {
                    "message": "Erro ao gerar resposta em streaming.",
                    "detail": detail,
                    "errorType": exc.__class__.__name__,
                },
            )

    response = Response(
        generate(),
        mimetype="text/event-stream",
    )

    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"

    return response


_PRIVACY_NOTICE = (
    "Suas mensagens são armazenadas por até 1 ano. "
    "Evite inserir dados pessoais sensíveis (CPF, endereços, etc.)."
)
