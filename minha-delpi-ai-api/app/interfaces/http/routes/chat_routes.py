from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
import json
import logging
from uuid import UUID
from dataclasses import asdict

from flask import Blueprint, Response, g, jsonify, request, stream_with_context
from sqlalchemy.exc import IntegrityError

from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_chat_agent_repository import PostgresChatAgentRepository
from app.infrastructure.persistence.postgres_external_action_repository import PostgresExternalActionRepository
from app.infrastructure.external_actions.external_action_test_executor import ExternalActionTestExecutor
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
    make_duplicate_chat_agent_use_case,
    make_export_chat_agent_use_case,
    make_get_chat_agent_stats_use_case,
    make_import_chat_agent_use_case,
    make_transfer_chat_agent_ownership_use_case,
    make_search_chat_directory_users_use_case,
    make_list_chat_agent_action_providers_use_case,
    make_upsert_chat_agent_action_provider_use_case,
    make_list_chat_agent_actions_use_case,
    make_get_chat_agent_use_case,
    make_list_chat_agent_shares_use_case,
    make_list_chat_agents_use_case,
    make_preview_chat_agent_use_case,
    make_revoke_chat_agent_share_use_case,
    make_share_chat_agent_use_case,
    make_list_chat_project_shares_use_case,
    make_revoke_chat_project_share_use_case,
    make_share_chat_project_use_case,
    make_update_chat_agent_use_case,
    make_upsert_chat_agent_action_use_case,
    make_list_chat_artifacts_use_case,
    make_list_chat_projects_use_case,
    make_update_chat_project_use_case,
    make_update_chat_artifact_use_case,
    make_get_chat_history_use_case,
    make_upsert_chat_message_feedback_use_case,
    make_list_chat_sessions_use_case,
    make_rename_chat_session_use_case,
    make_set_chat_session_archived_use_case,
    make_set_chat_session_pinned_use_case,
    make_send_chat_message_use_case,
    make_stream_chat_message_use_case,
)
from app.extensions.db import db
from app.application.use_cases.chat_agents_use_cases import (
    ChatAgentKeyConflictError,
    ChatAgentPermissionDeniedError,
)
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.interfaces.http.auth_decorators import require_permission
from app.infrastructure.gateways.core_me_gateway import CoreMeGateway
from app.interfaces.http.utils.errors import bad_request, conflict, forbidden


logger = logging.getLogger("minha-delpi-ai-api.chat")


chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _can_manage_agent_configuration(agent_id: str) -> tuple[bool, dict]:
    capabilities = _get_chat_capabilities_from_request()

    if not capabilities["canManageAgents"]:
        return False, capabilities

    try:
        agent_uuid = UUID(agent_id)
        user_uuid = UUID(g.current_user.sub)
    except ValueError:
        return False, capabilities

    record = PostgresChatAgentRepository().get_accessible_by_id(
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

    return {
        "permissions": sorted(permissions),
        "isSuperadmin": is_superadmin,
        "canManageAgents": can_manage_own_agents,
        "canManageOwnAgents": can_manage_own_agents,
        "canManageOfficialAgents": can_manage_official_agents,
        "canManageTools": can_manage_tools,
        "canUseTools": (
            can_manage_tools
            or CHAT_TOOLS_USE_PERMISSION in permissions
        ),
    }




@chat_bp.get("/status")
@require_permission(CHAT_ACCESS_PERMISSION)
def status():
    result = GetChatStatusUseCase().execute(g.current_user)
    return jsonify(result), 200








@chat_bp.get("/action-providers")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_action_providers():
    repository = PostgresExternalActionRepository()
    return jsonify(repository.list_providers()), 200


@chat_bp.get("/actions")
@require_permission(CHAT_ACCESS_PERMISSION)
def list_actions():
    provider_key = request.args.get("providerKey") or request.args.get("provider_key")
    repository = PostgresExternalActionRepository()
    actions = repository.list_actions(provider_key=provider_key)

    return jsonify(actions), 200


@chat_bp.get("/capabilities")
@require_permission(CHAT_ACCESS_PERMISSION)
def get_chat_capabilities():
    return jsonify(_get_chat_capabilities_from_request()), 200


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
                key=payload.get("key"),
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
        return forbidden(str(exc))
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
        return forbidden(str(exc))
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
        return forbidden(str(exc))
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
        return forbidden(str(exc))
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
        return forbidden(str(exc))

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
        return forbidden(str(exc))
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
        )
    except ChatAgentPermissionDeniedError as exc:
        return forbidden(str(exc))

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
        )
    except ChatAgentPermissionDeniedError as exc:
        return forbidden(str(exc))
    except InvalidChatSessionInputError as exc:
        return bad_request(str(exc))

    return jsonify(result), 200


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
        return forbidden("You do not have permission to configure actions for this agent")

    repository = PostgresExternalActionRepository()
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

    repository = PostgresExternalActionRepository()
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
        return forbidden("You do not have permission to configure actions for this agent")

    linked = _find_linked_agent_provider(agent_id, provider_key)

    if not linked:
        return _not_found_response()

    repository = PostgresExternalActionRepository()

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
        return forbidden("You do not have permission to configure actions for this agent")

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

    repository = PostgresExternalActionRepository()

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
        return forbidden("You do not have permission to configure actions for this agent")

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
        return forbidden("You do not have permission to configure actions for this agent")

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
                visibility=payload.get("visibility", "private"),
                icon=payload.get("icon"),
                metadata=payload.get("metadata"),
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

    try:
        result = use_case.execute(
            UpdateChatProjectRequest(
                user_id=g.current_user.sub,
                project_id=project_id,
                name=payload.get("name"),
                description=payload.get("description"),
                visibility=payload.get("visibility"),
                icon=payload.get("icon"),
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


@chat_bp.post("/attachments")
@require_permission(CHAT_ASK_PERMISSION)
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


@chat_bp.post("/sessions")
@require_permission(CHAT_ACCESS_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
def list_sessions():
    archived = request.args.get("archived", "false").lower() == "true"

    use_case = make_list_chat_sessions_use_case()
    result = use_case.execute(
        g.current_user.sub,
        archived=archived,
    )

    return jsonify([asdict(session) for session in result]), 200




@chat_bp.patch("/sessions/<session_id>")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
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




def forbidden(message: str = "Forbidden"):
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


@chat_bp.patch("/sessions/<session_id>/pin")
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
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
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
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
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
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
@require_permission(CHAT_HISTORY_VIEW_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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
@require_permission(CHAT_ACCESS_PERMISSION)
def get_history(session_id: str):
    use_case = make_get_chat_history_use_case()
    result = use_case.execute(
        user_id=g.current_user.sub,
        session_id=session_id,
    )

    return jsonify([asdict(message) for message in result]), 200


@chat_bp.put("/sessions/<session_id>/messages/<message_id>/feedback")
@require_permission(CHAT_ASK_PERMISSION)
@rate_limit("chat_messages", Settings.RATE_LIMIT_CHAT_MESSAGES_PER_WINDOW)
def upsert_message_feedback(session_id: str, message_id: str):
    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        return bad_request("Request body must be a JSON object")

    rating_raw = payload.get("rating")

    rating = None

    if rating_raw is not None:
        try:
            rating = int(rating_raw)
        except (TypeError, ValueError):
            return bad_request("rating must be -1, 1 or null")

    use_case = make_upsert_chat_message_feedback_use_case()

    try:
        result = use_case.execute(
            user_id=g.current_user.sub,
            session_id=session_id,
            message_id=message_id,
            rating=rating,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return bad_request(str(exc))
    except Exception:
        db.session.rollback()
        raise

    return jsonify(result), 200


@chat_bp.post("/sessions/<session_id>/messages")
@require_permission(CHAT_ASK_PERMISSION)
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
@require_permission(CHAT_ASK_PERMISSION)
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

                if event_type == "status":
                    yield _sse(
                        "status",
                        {"message": event.get("message", "")},
                    )

                elif event_type == "sources":
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
            logger.exception(
                "chat_stream_failed",
                extra={
                    "session_id": session_id,
                    "user_id": getattr(g.current_user, "sub", None),
                    "error_type": exc.__class__.__name__,
                },
            )
            yield _sse(
                "error",
                {
                    "message": "Erro ao gerar resposta em streaming.",
                    "detail": str(exc),
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
