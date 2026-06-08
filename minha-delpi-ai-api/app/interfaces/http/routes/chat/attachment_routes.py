"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

@chat_bp.post("/attachments")
@require_permission(CHAT_ASK_PERMISSION)
def upload_attachment_with_session():
    if "file" not in request.files:
        return bad_request("File is required")

    file = request.files["file"]

    if not file or not file.filename:
        return bad_request("File is required")

    project_id = request.form.get("projectId") or request.form.get("project_id")
    agent_id = request.form.get("agentId") or request.form.get("agent_id")
    context = request.form.get("context")

    session_use_case = make_create_chat_session_use_case()
    attachment_use_case = make_create_chat_attachment_use_case()

    try:
        session = session_use_case.execute(
            CreateChatSessionRequest(
                user_id=g.current_user.sub,
                title=str(
                    ContentService.stream().get("sessionTitleDefault") or "Nova conversa"
                ),
                context=context,
                project_id=project_id,
                agent_id=agent_id,
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
@require_permission(CHAT_ACCESS_PERMISSION)
def list_attachments(session_id: str):
    use_case = make_list_chat_attachments_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(attachment) for attachment in result]), 200


@chat_bp.post("/sessions/<session_id>/attachments")
@require_permission(CHAT_ASK_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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


@chat_bp.get("/attachments/<attachment_id>/download")
@require_permission(CHAT_ACCESS_PERMISSION)
def download_attachment(attachment_id: str):
    from io import BytesIO

    from app.domain.exceptions.chat_exceptions import (
        ChatSessionAccessDeniedError,
        ChatSessionNotFoundError,
    )

    use_case = make_download_chat_attachment_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            attachment_id=attachment_id,
        )
    except ChatSessionNotFoundError:
        return _not_found_response()
    except ChatSessionAccessDeniedError:
        return chat_forbidden("Access denied")
    except FileNotFoundError:
        return _not_found_response()

    return send_file(
        BytesIO(result.content),
        mimetype=result.content_type,
        as_attachment=True,
        download_name=result.filename,
    )


@chat_bp.get("/sessions/<session_id>/artifacts")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_artifacts(session_id: str):
    use_case = make_list_chat_artifacts_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(artifact) for artifact in result]), 200


@chat_bp.post("/sessions/<session_id>/artifacts")
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
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

