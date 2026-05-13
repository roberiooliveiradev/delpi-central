import json
from dataclasses import asdict

from flask import Blueprint, Response, g, jsonify, request, stream_with_context

from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_external_action_repository import PostgresExternalActionRepository
from app.interfaces.http.rate_limit_decorators import rate_limit

from app.application.dto.create_chat_artifact_request import CreateChatArtifactRequest
from app.application.dto.create_chat_attachment_request import CreateChatAttachmentRequest
from app.application.dto.create_chat_agent_request import CreateChatAgentRequest
from app.application.dto.create_chat_project_request import CreateChatProjectRequest
from app.application.dto.share_chat_agent_request import ShareChatAgentRequest
from app.application.dto.share_chat_project_request import ShareChatProjectRequest
from app.application.dto.update_chat_agent_request import UpdateChatAgentRequest
from app.application.dto.upsert_chat_agent_action_request import UpsertChatAgentActionRequest
from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.application.dto.update_chat_artifact_request import UpdateChatArtifactRequest
from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.update_chat_message_use_case import UpdateChatMessageRequest
from app.application.use_cases.rename_chat_session_use_case import RenameChatSessionRequest
from app.application.use_cases.set_chat_session_state_use_case import (
    SetChatSessionStateRequest,
)
from app.application.use_cases.get_chat_status_use_case import GetChatStatusUseCase
from app.composition.chat_composer import (
    make_delete_chat_session_use_case,
    make_update_chat_message_use_case,
    make_create_chat_artifact_use_case,
    make_create_chat_attachment_use_case,
    make_delete_chat_attachment_use_case,
    make_list_chat_attachments_use_case,
    make_create_chat_session_use_case,
    make_delete_chat_artifact_use_case,
    make_create_project_source_use_case,
    make_list_project_sources_use_case,
    make_create_agent_source_use_case,
    make_list_agent_sources_use_case,
    make_delete_chat_source_use_case,
    make_create_chat_project_use_case,
    make_delete_chat_project_use_case,
    make_create_chat_agent_use_case,
    make_delete_chat_agent_use_case,
    make_list_chat_agent_actions_use_case,
    make_list_chat_agents_use_case,
    make_share_chat_agent_use_case,
    make_share_chat_project_use_case,
    make_update_chat_agent_use_case,
    make_upsert_chat_agent_action_use_case,
    make_list_chat_artifacts_use_case,
    make_list_chat_projects_use_case,
    make_update_chat_project_use_case,
    make_update_chat_artifact_use_case,
    make_get_chat_history_use_case,
    make_list_chat_sessions_use_case,
    make_rename_chat_session_use_case,
    make_set_chat_session_archived_use_case,
    make_set_chat_session_pinned_use_case,
    make_send_chat_message_use_case,
    make_stream_chat_message_use_case,
)
from app.extensions.db import db
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
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






@chat_bp.get("/actions")
@require_permission("minha-delpi.chat.access")
def list_actions():
    provider_key = request.args.get("providerKey") or request.args.get("provider_key")
    repository = PostgresExternalActionRepository()
    actions = repository.list_actions(provider_key=provider_key)

    return jsonify(actions), 200


@chat_bp.get("/agents")
@require_permission("minha-delpi.chat.access")
def list_agents():
    use_case = make_list_chat_agents_use_case()
    result = use_case.execute(g.current_user.sub)

    return jsonify([asdict(agent) for agent in result]), 200


@chat_bp.post("/agents")
@require_permission("minha-delpi.chat.access")
def create_agent():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_agent_use_case()

    try:
        result = use_case.execute(
            CreateChatAgentRequest(
                user_id=g.current_user.sub,
                key=payload.get("key"),
                name=payload.get("name", ""),
                description=payload.get("description"),
                visibility=payload.get("visibility", "private"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
                system_prompt=payload.get("systemPrompt") or payload.get("system_prompt"),
                category=payload.get("category"),
                response_style=payload.get("responseStyle") or payload.get("response_style"),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.patch("/agents/<agent_id>")
@require_permission("minha-delpi.chat.access")
def update_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_agent_use_case()

    try:
        result = use_case.execute(
            UpdateChatAgentRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                name=payload.get("name"),
                description=payload.get("description"),
                visibility=payload.get("visibility"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
                archived=payload.get("archived"),
                system_prompt=payload.get("systemPrompt") or payload.get("system_prompt"),
                category=payload.get("category"),
                response_style=payload.get("responseStyle") or payload.get("response_style"),
                enabled=payload.get("enabled"),
            )
        )

        if not result:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.delete("/agents/<agent_id>")
@require_permission("minha-delpi.chat.access")
def delete_agent(agent_id: str):
    use_case = make_delete_chat_agent_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.post("/agents/<agent_id>/share")
@require_permission("minha-delpi.chat.access")
def share_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_share_chat_agent_use_case()

    try:
        shared = use_case.execute(
            ShareChatAgentRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                target_user_id=payload.get("targetUserId") or payload.get("target_user_id"),
                role=payload.get("role", "viewer"),
            )
        )

        if not shared:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True}), 200




@chat_bp.get("/agents/<agent_id>/actions")
@require_permission("minha-delpi.chat.access")
def list_agent_actions(agent_id: str):
    use_case = make_list_chat_agent_actions_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    return jsonify(result), 200


@chat_bp.put("/agents/<agent_id>/actions")
@require_permission("minha-delpi.chat.access")
def upsert_agent_action(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_upsert_chat_agent_action_use_case()

    try:
        saved = use_case.execute(
            UpsertChatAgentActionRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                provider_key=payload.get("providerKey") or payload.get("provider_key"),
                action_id=payload.get("actionId") or payload.get("action_id"),
                sensitivity=payload.get("sensitivity", "read"),
                requires_confirmation=bool(payload.get("requiresConfirmation") or payload.get("requires_confirmation")),
                enabled=payload.get("enabled", True),
            )
        )

        if not saved:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True}), 200




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


@chat_bp.get("/projects/<project_id>/sources")
@require_permission("minha-delpi.chat.access")
def list_project_sources(project_id: str):
    use_case = make_list_project_sources_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            project_id=project_id,
        )
    except ValueError as exc:
        return bad_request(str(exc))

    return jsonify([asdict(source) for source in result]), 200


@chat_bp.post("/projects/<project_id>/sources")
@require_permission("minha-delpi.chat.ask")
def create_project_source(project_id: str):
    use_case = make_create_project_source_use_case()

    try:
        result = _create_source_from_request(
            use_case,
            user_id=g.current_user.sub,
            owner_id_name="project_id",
            owner_id=project_id,
        )

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.get("/agents/<agent_id>/sources")
@require_permission("minha-delpi.chat.access")
def list_agent_sources(agent_id: str):
    use_case = make_list_agent_sources_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
        )
    except ValueError as exc:
        return bad_request(str(exc))

    return jsonify([asdict(source) for source in result]), 200


@chat_bp.post("/agents/<agent_id>/sources")
@require_permission("minha-delpi.chat.ask")
def create_agent_source(agent_id: str):
    use_case = make_create_agent_source_use_case()

    try:
        result = _create_source_from_request(
            use_case,
            user_id=g.current_user.sub,
            owner_id_name="agent_id",
            owner_id=agent_id,
        )

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.delete("/sources/<source_id>")
@require_permission("minha-delpi.chat.ask")
def delete_chat_source(source_id: str):
    use_case = make_delete_chat_source_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            source_id=source_id,
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.get("/projects")
@require_permission("minha-delpi.chat.access")
def list_projects():
    use_case = make_list_chat_projects_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        archived=(request.args.get("archived") == "true"),
    )

    return jsonify([asdict(project) for project in result]), 200


@chat_bp.post("/projects")
@require_permission("minha-delpi.chat.access")
def create_project():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_project_use_case()

    try:
        result = use_case.execute(
            CreateChatProjectRequest(
                user_id=g.current_user.sub,
                name=payload.get("name", ""),
                description=payload.get("description"),
                visibility=payload.get("visibility", "private"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.patch("/projects/<project_id>")
@require_permission("minha-delpi.chat.access")
def update_project(project_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_project_use_case()

    try:
        result = use_case.execute(
            UpdateChatProjectRequest(
                user_id=g.current_user.sub,
                project_id=project_id,
                name=payload.get("name"),
                description=payload.get("description"),
                visibility=payload.get("visibility"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
                archived=payload.get("archived"),
            )
        )

        if not result:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.delete("/projects/<project_id>")
@require_permission("minha-delpi.chat.access")
def delete_project(project_id: str):
    use_case = make_delete_chat_project_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            project_id=project_id,
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204



@chat_bp.post("/projects/<project_id>/share")
@require_permission("minha-delpi.chat.access")
def share_project(project_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_share_chat_project_use_case()

    try:
        shared = use_case.execute(
            ShareChatProjectRequest(
                user_id=g.current_user.sub,
                project_id=project_id,
                target_user_id=payload.get("targetUserId") or payload.get("target_user_id"),
                role=payload.get("role", "viewer"),
            )
        )

        if not shared:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True}), 200






@chat_bp.post("/attachments")
@require_permission("minha-delpi.chat.ask")
def upload_attachment_with_session():
    if "file" not in request.files:
        return bad_request("File is required")

    file = request.files["file"]

    if not file or not file.filename:
        return bad_request("File is required")

    project_id = request.form.get("projectId") or request.form.get("project_id")
    agent_key = request.form.get("agentKey") or request.form.get("agent_key")
    context = request.form.get("context")

    session_use_case = make_create_chat_session_use_case()
    attachment_use_case = make_create_chat_attachment_use_case()

    try:
        session = session_use_case.execute(
            CreateChatSessionRequest(
                user_id=g.current_user.sub,
                title="Nova conversa",
                context=context,
                project_id=project_id,
                agent_key=agent_key,
            )
        )

        content = file.read()

        attachment = attachment_use_case.execute(
            CreateChatAttachmentRequest(
                user_id=g.current_user.sub,
                session_id=session.id,
                original_filename=file.filename,
                content_type=file.content_type,
                size_bytes=len(content),
                content=content,
                metadata={
                    "source": "composer",
                    "createdSession": True,
                },
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "session": asdict(session),
            "attachment": asdict(attachment),
        }
    ), 201


@chat_bp.get("/sessions/<session_id>/attachments")
@require_permission("minha-delpi.chat.access")
def list_attachments(session_id: str):
    use_case = make_list_chat_attachments_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(attachment) for attachment in result]), 200


@chat_bp.post("/sessions/<session_id>/attachments")
@require_permission("minha-delpi.chat.ask")
def upload_attachment(session_id: str):
    if "file" not in request.files:
        return bad_request("File is required")

    file = request.files["file"]

    if not file or not file.filename:
        return bad_request("File is required")

    content = file.read()

    use_case = make_create_chat_attachment_use_case()

    try:
        result = use_case.execute(
            CreateChatAttachmentRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                original_filename=file.filename,
                content_type=file.content_type,
                size_bytes=len(content),
                content=content,
                metadata={
                    "source": "composer",
                },
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.delete("/attachments/<attachment_id>")
@require_permission("minha-delpi.chat.ask")
def delete_attachment(attachment_id: str):
    use_case = make_delete_chat_attachment_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            attachment_id=attachment_id,
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.get("/sessions/<session_id>/artifacts")
@require_permission("minha-delpi.chat.access")
def list_artifacts(session_id: str):
    use_case = make_list_chat_artifacts_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(artifact) for artifact in result]), 200


@chat_bp.post("/sessions/<session_id>/artifacts")
@require_permission("minha-delpi.chat.access")
def create_artifact(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_artifact_use_case()

    try:
        result = use_case.execute(
            CreateChatArtifactRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                message_id=payload.get("messageId"),
                type=payload.get("type", "markdown"),
                title=payload.get("title", ""),
                content=payload.get("content", ""),
                metadata=payload.get("metadata"),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.patch("/artifacts/<artifact_id>")
@require_permission("minha-delpi.chat.access")
def update_artifact(artifact_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_artifact_use_case()

    try:
        result = use_case.execute(
            UpdateChatArtifactRequest(
                user_id=g.current_user.sub,
                artifact_id=artifact_id,
                title=payload.get("title"),
                content=payload.get("content"),
                metadata=payload.get("metadata"),
            )
        )

        if not result:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.delete("/artifacts/<artifact_id>")
@require_permission("minha-delpi.chat.access")
def delete_artifact(artifact_id: str):
    use_case = make_delete_chat_artifact_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            artifact_id=artifact_id,
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


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
                project_id=payload.get("projectId") or payload.get("project_id"),
                agent_key=payload.get("agentKey") or payload.get("agent_key"),
            )
        )

        db.session.commit()
    except (ValueError, InvalidChatSessionInputError) as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.get("/sessions")
@require_permission("minha-delpi.chat.access")
def list_sessions():
    archived = request.args.get("archived", "false").lower() == "true"

    use_case = make_list_chat_sessions_use_case()
    result = use_case.execute(
        g.current_user.sub,
        archived=archived,
    )

    return jsonify([asdict(session) for session in result]), 200




@chat_bp.patch("/sessions/<session_id>")
@require_permission("minha-delpi.chat.history.view")
def rename_session(session_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_rename_chat_session_use_case()

    try:
        session = use_case.execute(
            RenameChatSessionRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
                title=payload.get("title", ""),
            )
        )

        if not session:
            db.session.rollback()
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

        db.session.commit()

    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200




@chat_bp.delete("/sessions/<session_id>")
@require_permission("minha-delpi.chat.access")
def delete_session(session_id: str):
    use_case = make_delete_chat_session_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            session_id=session_id,
        )

        if not deleted:
            db.session.rollback()
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

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return "", 204



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


@chat_bp.patch("/sessions/<session_id>/pin")
@require_permission("minha-delpi.chat.history.view")
def pin_session(session_id: str):
    use_case = make_set_chat_session_pinned_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            pinned=True,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/unpin")
@require_permission("minha-delpi.chat.history.view")
def unpin_session(session_id: str):
    use_case = make_set_chat_session_pinned_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            pinned=False,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/archive")
@require_permission("minha-delpi.chat.history.view")
def archive_session(session_id: str):
    use_case = make_set_chat_session_archived_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            archived=True,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/sessions/<session_id>/unarchive")
@require_permission("minha-delpi.chat.history.view")
def unarchive_session(session_id: str):
    use_case = make_set_chat_session_archived_use_case()

    try:
        session = use_case.execute(
            SetChatSessionStateRequest(
                user_id=g.current_user.sub,
                session_id=session_id,
            ),
            archived=False,
        )

        if not session:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(session)), 200


@chat_bp.patch("/messages/<message_id>")
@require_permission("minha-delpi.chat.ask")
def update_message(message_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_message_use_case()

    try:
        message = use_case.execute(
            UpdateChatMessageRequest(
                user_id=g.current_user.sub,
                message_id=message_id,
                content=payload.get("content", ""),
            )
        )

        if not message:
            db.session.rollback()
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

        db.session.commit()

    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))

    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(message)), 200


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
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
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
                attachment_ids=payload.get("attachmentIds") or payload.get("attachment_ids"),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.post("/sessions/<session_id>/messages/stream")
@require_permission("minha-delpi.chat.ask")
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
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
        attachment_ids=payload.get("attachmentIds") or payload.get("attachment_ids"),
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
