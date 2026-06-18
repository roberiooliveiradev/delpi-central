"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

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
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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


@chat_bp.get("/sources/<source_id>/download")
@require_permission(CHAT_ACCESS_PERMISSION)
def download_chat_source(source_id: str):
    from io import BytesIO

    from app.domain.exceptions.chat_exceptions import (
        ChatSessionAccessDeniedError,
        ChatSessionNotFoundError,
    )

    use_case = make_download_chat_source_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            source_id=source_id,
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


@chat_bp.get("/projects")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_projects():
    use_case = make_list_chat_projects_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        archived=(request.args.get("archived") == "true"),
    )

    return jsonify([asdict(project) for project in result]), 200


@chat_bp.post("/projects")
@require_permission(CHAT_ACCESS_PERMISSION)
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
                instructions=payload.get("instructions"),
                default_agent_id=payload.get("defaultAgentId") or payload.get("default_agent_id"),
                visibility=payload.get("visibility", "private"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
                share_conversation_context=_parse_optional_bool(
                    payload,
                    "shareConversationContext",
                    "share_conversation_context",
                ),
            )
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.patch("/projects/<project_id>")
@require_permission(CHAT_ACCESS_PERMISSION)
def update_project(project_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_project_use_case()

    explicit_default_agent_id = (
        "defaultAgentId" in payload or "default_agent_id" in payload
    )
    default_agent_id = (
        payload.get("defaultAgentId")
        if "defaultAgentId" in payload
        else payload.get("default_agent_id")
        if "default_agent_id" in payload
        else None
    )

    try:
        result = use_case.execute(
            UpdateChatProjectRequest(
                user_id=g.current_user.sub,
                project_id=project_id,
                name=payload.get("name"),
                description=payload.get("description"),
                instructions=payload.get("instructions"),
                default_agent_id=default_agent_id,
                explicit_default_agent_id=explicit_default_agent_id,
                visibility=payload.get("visibility"),
                icon=payload.get("icon"),
                color=payload.get("color"),
                metadata=payload.get("metadata"),
                share_conversation_context=_parse_optional_bool(
                    payload,
                    "shareConversationContext",
                    "share_conversation_context",
                ),
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
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
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


@chat_bp.get("/projects/<project_id>/shares")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_project_shares(project_id: str):
    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None
    use_case = make_list_chat_project_shares_use_case()
    shares = use_case.execute(
        user_id=g.current_user.sub,
        project_id=project_id,
        access_token=access_token,
    )
    return jsonify(shares), 200


@chat_bp.delete("/projects/<project_id>/shares/<target_user_id>")
@require_permission(CHAT_ACCESS_PERMISSION)
def revoke_project_share(project_id: str, target_user_id: str):
    use_case = make_revoke_chat_project_share_use_case()

    try:
        revoked = use_case.execute(
            user_id=g.current_user.sub,
            project_id=project_id,
            target_user_id=target_user_id,
        )

        if not revoked:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


