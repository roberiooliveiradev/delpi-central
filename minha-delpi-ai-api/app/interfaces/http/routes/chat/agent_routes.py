"""Rotas HTTP do chat — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403

@chat_bp.get("/agents")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agents():
    include_disabled = request.args.get("includeDisabled", "").lower() in {
        "1",
        "true",
        "yes",
    }
    include_stats = request.args.get("includeStats", "").lower() in {
        "1",
        "true",
        "yes",
    }
    hours = request.args.get("hours", 168)

    try:
        hours_value = int(hours)
    except (TypeError, ValueError):
        return bad_request("hours must be a number")

    use_case = make_list_chat_agents_use_case()
    result = use_case.execute(
        g.current_user.sub,
        include_disabled=include_disabled,
        include_stats=include_stats,
        stats_hours=hours_value,
    )

    return jsonify([asdict(agent) for agent in result]), 200


@chat_bp.get("/agents/<agent_id>")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_agent(agent_id: str):
    use_case = make_get_chat_agent_use_case()
    result = use_case.execute(g.current_user.sub, agent_id)

    if not result:
        return _not_found_response()

    return jsonify(asdict(result)), 200


@chat_bp.post("/agents")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def create_agent():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_create_chat_agent_use_case()
    capabilities = _get_chat_capabilities_from_request()

    try:
        result = use_case.execute(
            CreateChatAgentRequest(
                user_id=g.current_user.sub,
                name=payload.get("name", ""),
                description=payload.get("description"),
                visibility=payload.get("visibility", "private"),
                icon=payload.get("icon"),
                metadata=payload.get("metadata"),
                system_prompt=payload.get("systemPrompt") or payload.get("system_prompt"),
                category=payload.get("category"),
                response_style=payload.get("responseStyle") or payload.get("response_style"),
                can_manage_official_agents=capabilities["canManageOfficialAgents"],
            )
        )

        db.session.commit()
    except ChatAgentPermissionDeniedError as exc:
        db.session.rollback()
        return chat_forbidden(str(exc))
    except ChatAgentKeyConflictError as exc:
        db.session.rollback()
        return conflict(str(exc))
    except InvalidChatSessionInputError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.patch("/agents/<agent_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def update_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_update_chat_agent_use_case()
    capabilities = _get_chat_capabilities_from_request()

    metadata = dict(payload.get("metadata") or {})

    for visual_key in ["color", "avatar", "badge", "theme"]:
        if payload.get(visual_key) is not None:
            metadata[visual_key] = payload.get(visual_key)

    if payload.get("archived") is not None:
        metadata["archived"] = payload.get("archived")

    try:
        result = use_case.execute(
            UpdateChatAgentRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                name=payload.get("name"),
                description=payload.get("description"),
                visibility=payload.get("visibility"),
                icon=payload.get("icon"),
                metadata=metadata,
                system_prompt=payload.get("systemPrompt") or payload.get("system_prompt"),
                category=payload.get("category"),
                response_style=payload.get("responseStyle") or payload.get("response_style"),
                enabled=payload.get("enabled"),
                max_tool_calls=payload.get("maxToolCalls") or payload.get("max_tool_calls"),
                requires_confirmation_for_write=payload.get("requiresConfirmationForWrite")
                if payload.get("requiresConfirmationForWrite") is not None
                else payload.get("requires_confirmation_for_write"),
                can_manage_official_agents=capabilities["canManageOfficialAgents"],
            )
        )

        if not result:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except ChatAgentPermissionDeniedError as exc:
        db.session.rollback()
        return chat_forbidden(str(exc))
    except InvalidChatSessionInputError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.delete("/agents/<agent_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def delete_agent(agent_id: str):
    use_case = make_delete_chat_agent_use_case()
    capabilities = _get_chat_capabilities_from_request()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.post("/agents/<agent_id>/duplicate")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def duplicate_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}
    capabilities = _get_chat_capabilities_from_request()
    use_case = make_duplicate_chat_agent_use_case()

    copy_actions = True
    copy_sources = False

    if isinstance(payload, dict):
        if "copyActions" in payload:
            copy_actions = bool(payload.get("copyActions"))
        if "copySources" in payload:
            copy_sources = bool(payload.get("copySources"))

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
            copy_actions=copy_actions,
            copy_sources=copy_sources,
        )

        if not result:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except ChatAgentPermissionDeniedError as exc:
        db.session.rollback()
        return chat_forbidden(str(exc))
    except IntegrityError:
        db.session.rollback()
        return conflict("Agent key already exists")
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.post("/agents/<agent_id>/transfer")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def transfer_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_transfer_chat_agent_ownership_use_case()

    try:
        transferred = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            new_owner_user_id=str(payload.get("newOwnerUserId") or ""),
        )

        if not transferred:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except InvalidChatSessionInputError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except ChatAgentPermissionDeniedError as exc:
        db.session.rollback()
        return chat_forbidden(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return "", 204


@chat_bp.get("/agents/<agent_id>/export")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def export_agent(agent_id: str):
    use_case = make_export_chat_agent_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
        )
    except ChatAgentPermissionDeniedError as exc:
        return chat_forbidden(str(exc))

    if not result:
        return _not_found_response()

    return jsonify(result), 200


@chat_bp.post("/agents/import")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def import_agent():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    use_case = make_import_chat_agent_use_case()
    capabilities = _get_chat_capabilities_from_request()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            payload=payload,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )
        db.session.commit()
    except ChatAgentPermissionDeniedError as exc:
        db.session.rollback()
        return chat_forbidden(str(exc))
    except ChatAgentKeyConflictError as exc:
        db.session.rollback()
        return conflict(str(exc))
    except InvalidChatSessionInputError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except IntegrityError:
        db.session.rollback()
        return conflict("Agent key already exists")
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 201


@chat_bp.get("/agents/<agent_id>/stats")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def get_agent_stats(agent_id: str):
    hours = request.args.get("hours", 168)
    specialization = None
    spec_raw = request.args.get("specialization")

    if spec_raw:
        try:
            import json

            parsed = json.loads(spec_raw)

            if isinstance(parsed, dict):
                specialization = parsed
        except (TypeError, ValueError):
            return bad_request("specialization must be valid JSON")

    try:
        hours_value = int(hours)
    except (TypeError, ValueError):
        return bad_request("hours must be a number")

    use_case = make_get_chat_agent_stats_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            hours=hours_value,
            specialization=specialization,
        )
    except ChatAgentPermissionDeniedError as exc:
        return chat_forbidden(str(exc))

    if not result:
        return _not_found_response()

    return jsonify(result), 200


@chat_bp.get("/users/search")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def search_chat_users():
    query = request.args.get("q") or request.args.get("query") or ""
    limit = request.args.get("limit", 10)
    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    if not access_token:
        return bad_request("Authorization header is required")

    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        return bad_request("limit must be a number")

    use_case = make_search_chat_directory_users_use_case()
    items = use_case.execute(
        access_token=access_token,
        query=query,
        limit=limit_value,
    )

    return jsonify({"items": items}), 200


@chat_bp.post("/agents/<agent_id>/share")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
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
    except InvalidChatSessionInputError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True}), 200











@chat_bp.get("/agents/<agent_id>/shares")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def list_agent_shares(agent_id: str):
    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None
    use_case = make_list_chat_agent_shares_use_case()
    shares = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
        access_token=access_token,
    )
    return jsonify(shares), 200


@chat_bp.delete("/agents/<agent_id>/shares/<target_user_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def revoke_agent_share(agent_id: str, target_user_id: str):
    use_case = make_revoke_chat_agent_share_use_case()

    try:
        revoked = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
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


@chat_bp.post("/agents/preview")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def preview_agent_draft():
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None
    use_case = make_preview_chat_agent_use_case()
    previous_messages = normalize_preview_previous_messages(
        payload.get("previousMessages") if payload.get("previousMessages") is not None else payload.get("previous_messages"),
    )

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=None,
            message=payload.get("message") or payload.get("question") or "",
            access_token=access_token,
            generate_answer=bool(payload.get("generateAnswer", True)),
            draft=payload.get("draft"),
            previous_messages=previous_messages,
        )
    except ChatAgentPermissionDeniedError as exc:
        return chat_forbidden(str(exc))
    except InvalidChatSessionInputError as exc:
        return bad_request(str(exc))

    return jsonify(result), 200


@chat_bp.post("/agents/<agent_id>/preview")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def preview_agent(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    access_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None
    use_case = make_preview_chat_agent_use_case()
    previous_messages = normalize_preview_previous_messages(
        payload.get("previousMessages")
        if payload.get("previousMessages") is not None
        else payload.get("previous_messages"),
    )

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            message=payload.get("message") or payload.get("question") or "",
            access_token=access_token,
            generate_answer=bool(payload.get("generateAnswer", True)),
            draft=payload.get("draft"),
            previous_messages=previous_messages,
        )
    except ChatAgentPermissionDeniedError as exc:
        return chat_forbidden(str(exc))
    except InvalidChatSessionInputError as exc:
        return bad_request(str(exc))

    return jsonify(result), 200


@chat_bp.post("/agents/<agent_id>/publish")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def publish_agent(agent_id: str):
    use_case = make_publish_chat_agent_use_case()
    capabilities = _get_chat_capabilities_from_request()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )
    except ChatAgentPermissionDeniedError as exc:
        return chat_forbidden(str(exc))
    except InvalidChatSessionInputError as exc:
        return bad_request(str(exc))

    if not result:
        return _not_found_response()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(asdict(result)), 200


@chat_bp.get("/agents/<agent_id>/versions")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def list_agent_versions(agent_id: str):
    use_case = make_list_chat_agent_versions_use_case()
    versions = use_case.execute(user_id=g.current_user.sub, agent_id=agent_id)
    return jsonify(versions), 200
