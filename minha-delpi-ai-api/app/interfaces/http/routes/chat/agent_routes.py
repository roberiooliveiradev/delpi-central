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

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=None,
            message=payload.get("message") or payload.get("question") or "",
            access_token=access_token,
            generate_answer=bool(payload.get("generateAnswer", True)),
            draft=payload.get("draft"),
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

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            message=payload.get("message") or payload.get("question") or "",
            access_token=access_token,
            generate_answer=bool(payload.get("generateAnswer", True)),
            draft=payload.get("draft"),
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


@chat_bp.post("/agents/<agent_id>/providers/create")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def create_agent_action_provider(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    provider_key = payload.get("providerKey") or payload.get("provider_key")
    name = payload.get("name")
    provider_type = payload.get("type") or payload.get("providerType") or "openapi"
    base_url = payload.get("baseUrl") or payload.get("base_url")
    openapi_url = payload.get("openApiUrl") or payload.get("openapi_url")
    schema_json = payload.get("schema") or payload.get("schemaJson") or payload.get("schema_json")

    if not provider_key:
        return bad_request("providerKey is required")

    if not name:
        return bad_request("name is required")

    if not base_url:
        return bad_request("baseUrl is required")

    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    repository = make_external_action_repository()
    upsert_use_case = make_upsert_chat_agent_action_provider_use_case()

    try:
        existing_provider = repository.get_provider_by_key(provider_key)

        if not existing_provider:
            provider = repository.create_provider(
                {
                    "providerKey": provider_key,
                    "name": name,
                    "type": provider_type,
                    "baseUrl": base_url,
                    "openApiUrl": openapi_url,
                    "privacyPolicyUrl": payload.get("privacyPolicyUrl") or payload.get("privacy_policy_url"),
                    "authMode": payload.get("authMode") or "none",
                    "authConfig": payload.get("authConfig"),
                    "enabled": True,
                }
            )
        else:
            provider = repository._provider_to_dict(existing_provider)

        import_result = None

        if isinstance(schema_json, dict):
            import_result = repository.import_schema_from_json(
                provider_key=provider_key,
                schema_json=schema_json,
                source_type="inline",
            )
        elif openapi_url:
            import_result = repository.import_schema_from_url(provider_key=provider_key)

        saved = upsert_use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            provider_key=provider_key,
            enabled=bool(payload.get("enabled", True)),
            allow_read=bool(payload.get("allowRead", True)),
            allow_write=bool(payload.get("allowWrite", True)),
            allow_admin=bool(payload.get("allowAdmin", False)),
            requires_confirmation_for_write=bool(
                payload.get("requiresConfirmationForWrite", True)
            ),
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )

        if not saved:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "provider": provider,
            "import": import_result,
            "linked": True,
        }
    ), 201





@chat_bp.get("/agents/<agent_id>/providers/<provider_key>")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_agent_action_provider(agent_id: str, provider_key: str):
    linked = _find_linked_agent_provider(agent_id, provider_key)

    if not linked:
        return _not_found_response()

    repository = make_external_action_repository()
    provider = repository.get_provider_details(provider_key)

    if not provider:
        return _not_found_response()

    return jsonify(provider), 200


@chat_bp.patch("/agents/<agent_id>/providers/<provider_key>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def update_agent_action_provider(agent_id: str, provider_key: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    can_manage_agent, _capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    linked = _find_linked_agent_provider(agent_id, provider_key)

    if not linked:
        return _not_found_response()

    repository = make_external_action_repository()

    try:
        update_payload = {
            "name": payload.get("name"),
            "baseUrl": payload.get("baseUrl") or payload.get("base_url"),
            "openApiUrl": payload.get("openApiUrl") or payload.get("openapi_url"),
            "privacyPolicyUrl": (
                payload.get("privacyPolicyUrl") or payload.get("privacy_policy_url")
            ),
            "authMode": payload.get("authMode") or payload.get("auth_mode"),
            "authConfig": payload.get("authConfig") or payload.get("auth_config"),
        }

        if "enabled" in payload:
            update_payload["enabled"] = payload.get("enabled")

        provider = repository.update_provider(
            provider_key,
            update_payload,
        )

        if not provider:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(provider), 200


@chat_bp.post("/agents/<agent_id>/providers/<provider_key>/import")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def import_agent_action_provider_schema(agent_id: str, provider_key: str):
    can_manage_agent, _capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    agent_repository = make_list_chat_agent_action_providers_use_case()
    providers = agent_repository.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    provider = next(
        (
            item for item in providers
            if item.get("providerKey") == provider_key
        ),
        None,
    )

    if not provider:
        return _not_found_response()

    repository = make_external_action_repository()

    try:
        result = repository.import_schema_from_url(provider_key=provider_key)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200



@chat_bp.post("/agents/<agent_id>/providers/<provider_key>/actions/<action_id>/test")
@require_permission(CHAT_ACCESS_PERMISSION)
def test_agent_action(agent_id: str, provider_key: str, action_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    linked = _find_linked_agent_provider(agent_id, provider_key)

    if not linked:
        return _not_found_response()

    executor = ExternalActionTestExecutor()

    try:
        result = executor.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            provider_key=provider_key,
            action_id=action_id,
            path_params=payload.get("pathParams") or payload.get("path_params") or {},
            query=payload.get("query") or {},
            body=payload.get("body"),
            user_authorization_header=request.headers.get("Authorization"),
        )

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(
        {
            "ok": result.ok,
            "statusCode": result.status_code,
            "durationMs": result.duration_ms,
            "url": result.url,
            "responsePreview": result.response_preview,
            "errorMessage": result.error_message,
        }
    ), 200


@chat_bp.get("/agents/<agent_id>/providers/<provider_key>/actions/<action_id>/logs")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agent_action_test_logs(agent_id: str, provider_key: str, action_id: str):
    linked = _find_linked_agent_provider(agent_id, provider_key)

    if not linked:
        return _not_found_response()

    executor = ExternalActionTestExecutor()
    logs = executor.list_logs(
        user_id=g.current_user.sub,
        agent_id=agent_id,
        provider_key=provider_key,
        action_id=action_id,
        limit=int(request.args.get("limit") or 20),
    )

    return jsonify(logs), 200


@chat_bp.get("/agents/<agent_id>/providers")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agent_action_providers(agent_id: str):
    use_case = make_list_chat_agent_action_providers_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    return jsonify(result), 200


@chat_bp.put("/agents/<agent_id>/providers")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def upsert_agent_action_provider(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    use_case = make_upsert_chat_agent_action_provider_use_case()

    try:
        saved = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            provider_key=payload.get("providerKey") or payload.get("provider_key"),
            enabled=bool(payload.get("enabled", True)),
            allow_read=bool(payload.get("allowRead", True)),
            allow_write=bool(payload.get("allowWrite", False)),
            allow_admin=bool(payload.get("allowAdmin", False)),
            requires_confirmation_for_write=bool(
                payload.get("requiresConfirmationForWrite", True)
            ),
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )

        if not saved:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"saved": True}), 200


@chat_bp.get("/agents/<agent_id>/actions")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agent_actions(agent_id: str):
    use_case = make_list_chat_agent_actions_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    return jsonify(result), 200


@chat_bp.put("/agents/<agent_id>/actions")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def upsert_agent_action(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

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
                can_manage_official_agents=capabilities["canManageOfficialAgents"],
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


@chat_bp.delete("/agents/<agent_id>/providers/<provider_key>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def delete_agent_action_provider(agent_id: str, provider_key: str):
    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    use_case = make_delete_chat_agent_action_provider_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            provider_key=provider_key,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"deleted": True}), 200


@chat_bp.delete("/agents/<agent_id>/providers/<provider_key>/actions/<path:action_id>")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def delete_agent_action(agent_id: str, provider_key: str, action_id: str):
    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure actions for this agent")

    use_case = make_delete_chat_agent_action_use_case()

    try:
        deleted = use_case.execute(
            user_id=g.current_user.sub,
            agent_id=agent_id,
            provider_key=provider_key,
            action_id=action_id,
            can_manage_official_agents=capabilities["canManageOfficialAgents"],
        )

        if not deleted:
            db.session.rollback()
            return _not_found_response()

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"deleted": True}), 200


@chat_bp.get("/skills")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_skill_catalog():
    use_case = make_list_chat_skill_catalog_use_case()
    return jsonify(use_case.execute()), 200


@chat_bp.get("/agents/<agent_id>/skills")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_agent_skills(agent_id: str):
    use_case = make_list_chat_agent_skills_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        agent_id=agent_id,
    )

    if result is None:
        return _not_found_response()

    return jsonify(result), 200


@chat_bp.put("/agents/<agent_id>/skills")
@require_permission(CHAT_TOOLS_MANAGE_PERMISSION)
def upsert_agent_skill(agent_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    can_manage_agent, capabilities = _can_manage_agent_configuration(agent_id)

    if not can_manage_agent:
        return chat_forbidden("You do not have permission to configure skills for this agent")

    skill_key = payload.get("skillKey") or payload.get("skill_key")

    if not skill_key:
        return bad_request("skillKey is required")

    use_case = make_upsert_chat_agent_skill_use_case()

    try:
        saved = use_case.execute(
            UpsertChatAgentSkillRequest(
                user_id=g.current_user.sub,
                agent_id=agent_id,
                skill_key=str(skill_key),
                enabled=bool(payload.get("enabled", True)),
                can_manage_official_agents=capabilities["canManageOfficialAgents"],
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

