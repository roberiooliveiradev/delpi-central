"""Rotas HTTP de providers e actions do agente — registradas em `chat.shared.chat_bp`."""

from app.interfaces.http.routes.chat.deps import *  # noqa: F403


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
    from flask import current_app

    from app.application.services.external_action_import_job_service import (
        ExternalActionImportJobService,
    )

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

    async_requested = request.args.get("async", "").lower() == "true"

    if async_requested:
        if not Settings.EXTERNAL_ACTION_IMPORT_ASYNC_ENABLED:
            return bad_request("Async import is disabled")

        try:
            job = ExternalActionImportJobService.start(
                current_app._get_current_object(),
                provider_key=provider_key,
                user_id=g.current_user.sub,
                agent_id=agent_id,
            )
        except ValueError as exc:
            db.session.rollback()
            return bad_request(str(exc))
        except Exception:
            db.session.rollback()
            raise

        return jsonify(job), 202

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


@chat_bp.get("/providers/<provider_key>/import/jobs/latest")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_latest_external_action_import_job(provider_key: str):
    from app.application.services.external_action_import_job_service import (
        ExternalActionImportJobService,
    )

    job = ExternalActionImportJobService.get_latest(provider_key=provider_key)

    if not job:
        return _not_found_response()

    return jsonify(job), 200


@chat_bp.get("/providers/<provider_key>/import/jobs/<job_id>")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_external_action_import_job(provider_key: str, job_id: str):
    from app.application.services.external_action_import_job_service import (
        ExternalActionImportJobService,
    )

    job = ExternalActionImportJobService.get(
        provider_key=provider_key,
        job_id=job_id,
    )

    if not job:
        return _not_found_response()

    return jsonify(job), 200


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
