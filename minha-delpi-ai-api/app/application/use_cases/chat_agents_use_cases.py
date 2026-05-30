import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.application.dto.chat_agent_response import ChatAgentResponse
from app.application.dto.create_chat_agent_request import CreateChatAgentRequest
from app.application.dto.share_chat_agent_request import ShareChatAgentRequest
from app.application.dto.update_chat_agent_request import UpdateChatAgentRequest
from app.application.dto.upsert_chat_agent_action_request import UpsertChatAgentActionRequest
from app.application.services.chat_agent_config_snapshot_service import (
    has_unpublished_changes,
    normalize_draft_payload,
)
from app.domain.entities.chat_agent import ChatAgent
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort


ALLOWED_VISIBILITY = {"private", "public", "system"}
ALLOWED_SHARE_ROLES = {"viewer", "editor"}
ALLOWED_SENSITIVITY = {"read", "write", "admin"}
AGENT_EXPORT_VERSION = 1


class ChatAgentPermissionDeniedError(Exception):
    pass


class ChatAgentKeyConflictError(Exception):
    pass


def _can_view_system_prompt(access_role: str) -> bool:
    return access_role in {"owner", "editor", "system"}


def _to_response(
    agent: ChatAgent,
    access_role: str = "viewer",
    *,
    include_system_prompt: bool = False,
    usage_summary: dict[str, int] | None = None,
    draft_agent: ChatAgent | None = None,
) -> ChatAgentResponse:
    return ChatAgentResponse(
        id=str(agent.id),
        key=agent.key,
        name=agent.name,
        description=agent.description,
        enabled=agent.enabled,
        metadata=agent.metadata,
        owner_user_id=str(agent.owner_user_id) if agent.owner_user_id else None,
        visibility=agent.visibility,
        category=agent.category,
        icon=agent.icon,
        response_style=agent.response_style,
        max_tool_calls=agent.max_tool_calls,
        requires_confirmation_for_write=agent.requires_confirmation_for_write,
        access_role=access_role,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
        system_prompt=agent.system_prompt if include_system_prompt else None,
        sessions_in_window=(
            usage_summary.get("sessionsInWindow") if usage_summary else None
        ),
        total_sessions=usage_summary.get("totalSessions") if usage_summary else None,
        published_version=int(getattr(agent, "published_version", 0) or 0),
        published_at=(
            agent.published_at.isoformat() if getattr(agent, "published_at", None) else None
        ),
        has_unpublished_changes=has_unpublished_changes(draft_agent or agent),
    )


def _normalize_text(value: str | None, max_length: int, required: bool = False) -> str | None:
    normalized = (value or "").strip()

    if required and not normalized:
        raise InvalidChatSessionInputError("Required field is empty")

    if not normalized:
        return None

    if len(normalized) > max_length:
        raise InvalidChatSessionInputError(f"Field exceeds maximum length of {max_length}")

    return normalized


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")

    if not normalized:
        raise InvalidChatSessionInputError("Invalid agent key")

    return normalized[:80]


class ListChatAgentsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        user_id: str,
        *,
        include_disabled: bool = False,
        include_stats: bool = False,
        stats_hours: int = 168,
    ) -> list[ChatAgentResponse]:
        agents = self.repository.list_accessible(
            UUID(user_id),
            include_disabled=include_disabled,
        )

        usage_by_key: dict[str, dict[str, int]] = {}

        if include_stats:
            stats_keys = [
                agent.key
                for agent, access_role, _draft in agents
                if access_role in {"owner", "editor", "system"}
            ]
            usage_by_key = self.repository.list_usage_summaries(
                stats_keys,
                hours=stats_hours,
            )

        return [
            _to_response(
                agent,
                access_role,
                usage_summary=usage_by_key.get(agent.key) if include_stats else None,
                draft_agent=draft if access_role in {"owner", "editor", "system"} else None,
            )
            for agent, access_role, draft in agents
        ]


class CreateChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: CreateChatAgentRequest) -> ChatAgentResponse:
        name = _normalize_text(request.name, 120, required=True)
        visibility = request.visibility or "private"

        if visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid agent visibility")

        if visibility == "system" and not request.can_manage_official_agents:
            raise ChatAgentPermissionDeniedError(
                "You do not have permission to create official agents"
            )

        key = _slugify(request.key or name)
        owner_user_id = None if visibility == "system" else UUID(request.user_id)

        try:
            agent = self.repository.create(
                owner_user_id=owner_user_id,
                key=key,
                name=name,
                description=_normalize_text(request.description, 800),
                system_prompt=_normalize_text(request.system_prompt, 12000),
                visibility=visibility,
                category=_normalize_text(request.category, 80),
                icon=_normalize_text(request.icon, 60),
                response_style=_normalize_text(request.response_style, 40),
                metadata=request.metadata,
            )
        except IntegrityError as exc:
            raise ChatAgentKeyConflictError("Agent key already exists") from exc

        return _to_response(agent, "owner", include_system_prompt=True)


class GetChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, agent_id: str) -> ChatAgentResponse | None:
        record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not record:
            return None

        agent, access_role = record
        return _to_response(
            agent,
            access_role,
            include_system_prompt=_can_view_system_prompt(access_role),
        )


class UpdateChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: UpdateChatAgentRequest) -> ChatAgentResponse | None:
        fields = {
            "name": _normalize_text(request.name, 120) if request.name is not None else None,
            "description": _normalize_text(request.description, 800) if request.description is not None else None,
            "system_prompt": _normalize_text(request.system_prompt, 12000) if request.system_prompt is not None else None,
            "visibility": request.visibility,
            "category": _normalize_text(request.category, 80) if request.category is not None else None,
            "icon": _normalize_text(request.icon, 60) if request.icon is not None else None,
            "response_style": _normalize_text(request.response_style, 40) if request.response_style is not None else None,
            "agent_metadata": request.metadata,
            "enabled": request.enabled,
            "max_tool_calls": request.max_tool_calls,
            "requires_confirmation_for_write": request.requires_confirmation_for_write,
        }

        if fields["visibility"] is not None and fields["visibility"] not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid agent visibility")

        if fields["max_tool_calls"] is not None:
            fields["max_tool_calls"] = max(1, min(int(fields["max_tool_calls"]), 20))

        agent_id = UUID(request.agent_id)
        user_id = UUID(request.user_id)

        if not self.repository.exists_by_id(agent_id):
            return None

        if not self.repository.can_edit(
            agent_id,
            user_id,
            can_manage_official_agents=request.can_manage_official_agents,
        ):
            raise ChatAgentPermissionDeniedError("You do not have permission to edit this agent")

        agent = self.repository.update(
            agent_id=agent_id,
            user_id=user_id,
            can_manage_official_agents=request.can_manage_official_agents,
            **fields,
        )

        if not agent:
            return None

        access_record = self.repository.get_accessible_by_id(agent_id, user_id)
        access_role = access_record[1] if access_record else "editor"

        return _to_response(
            agent,
            access_role,
            include_system_prompt=_can_view_system_prompt(access_role),
        )


class DeleteChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        user_id: str,
        agent_id: str,
        can_manage_official_agents: bool = False,
    ) -> bool:
        return self.repository.delete(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
            can_manage_official_agents=can_manage_official_agents,
        )


class DuplicateChatAgentUseCase:
    def __init__(
        self,
        repository: ChatAgentRepositoryPort,
        source_copy_service=None,
    ):
        self.repository = repository
        self.source_copy_service = source_copy_service

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        can_manage_official_agents: bool = False,
        copy_actions: bool = True,
        copy_sources: bool = False,
    ) -> ChatAgentResponse | None:
        source = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not source:
            return None

        source_agent, access_role = source

        if access_role not in {"owner", "editor", "system"}:
            raise ChatAgentPermissionDeniedError(
                "You do not have permission to duplicate this agent"
            )

        agent = self.repository.duplicate(
            UUID(agent_id),
            UUID(user_id),
            can_manage_official_agents=can_manage_official_agents,
            copy_actions=copy_actions,
        )

        if not agent:
            return None

        if copy_sources and self.source_copy_service:
            self.source_copy_service.copy_agent_sources(
                user_id=user_id,
                source_agent=source_agent,
                target_agent=agent,
            )

        return _to_response(agent, "owner", include_system_prompt=True)


class TransferChatAgentOwnershipUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        new_owner_user_id: str,
    ) -> bool:
        normalized_owner = (new_owner_user_id or "").strip()

        if not normalized_owner:
            raise InvalidChatSessionInputError("newOwnerUserId is required")

        if normalized_owner == user_id:
            raise InvalidChatSessionInputError("Cannot transfer an agent to yourself")

        return self.repository.transfer_ownership(
            UUID(agent_id),
            UUID(user_id),
            UUID(normalized_owner),
        )


class GetChatAgentStatsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        hours: int = 168,
    ) -> dict | None:
        record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not record:
            return None

        _, access_role = record

        if access_role not in {"owner", "editor", "system"}:
            raise ChatAgentPermissionDeniedError(
                "You do not have permission to view agent statistics"
            )

        return self.repository.get_usage_stats(
            UUID(agent_id),
            UUID(user_id),
            hours=hours,
        )


class ListChatAgentSharesUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort, share_profile_service=None):
        self.repository = repository
        self.share_profile_service = share_profile_service

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        access_token: str | None = None,
    ) -> list[dict]:
        shares = self.repository.list_shares(UUID(agent_id), UUID(user_id))

        if self.share_profile_service:
            return self.share_profile_service.enrich_shares(
                shares,
                access_token=access_token,
            )

        return shares


class RevokeChatAgentShareUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str, target_user_id: str) -> bool:
        return self.repository.revoke_share(
            UUID(agent_id),
            UUID(user_id),
            UUID(target_user_id),
        )


class PreviewChatAgentUseCase:
    def __init__(
        self,
        repository: ChatAgentRepositoryPort,
        simulate_use_case,
    ):
        self.repository = repository
        self.simulate_use_case = simulate_use_case

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        message: str,
        access_token: str | None,
        generate_answer: bool = True,
        draft: dict | None = None,
    ) -> dict:
        from app.application.services.chat_agent_config_snapshot_service import (
            apply_snapshot_to_agent,
        )

        normalized = str(message or "").strip()

        if not normalized:
            raise InvalidChatSessionInputError("message is required")

        draft_snapshot = normalize_draft_payload(draft)
        agent_prompt_override = None
        agent_metadata_override = None
        resolved_agent_id = agent_id
        resolved_agent_key = None

        if agent_id:
            agent = self.repository.get_for_preview(UUID(agent_id), UUID(user_id))

            if not agent:
                raise InvalidChatSessionInputError("Agent not found")

            record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

            if not record:
                raise InvalidChatSessionInputError("Agent not found")

            _, access_role = record

            if access_role not in {"owner", "editor", "system"}:
                raise ChatAgentPermissionDeniedError(
                    "You do not have permission to preview this agent"
                )

            if draft_snapshot:
                if not draft_snapshot.get("name"):
                    draft_snapshot["name"] = agent.name
                agent = apply_snapshot_to_agent(agent, draft_snapshot)

            agent_prompt_override = agent.system_prompt
            agent_metadata_override = agent.metadata
            resolved_agent_key = agent.key
        elif draft_snapshot:
            if not draft_snapshot.get("name"):
                raise InvalidChatSessionInputError("draft.name is required")
            agent_prompt_override = draft_snapshot.get("systemPrompt")
            agent_metadata_override = draft_snapshot.get("metadata")
            draft_key = (draft or {}).get("key") if isinstance(draft, dict) else None
            resolved_agent_key = _slugify(str(draft_key or draft_snapshot.get("name")))
        else:
            raise InvalidChatSessionInputError("agentId or draft is required")

        return self.simulate_use_case.execute(
            question=normalized,
            agent_id=resolved_agent_id,
            agent_key=resolved_agent_key,
            generate_answer=generate_answer,
            user_id=user_id,
            access_token=access_token,
            agent_prompt_override=agent_prompt_override,
            agent_metadata_override=agent_metadata_override,
            skip_enabled_check=True,
        )


class PublishChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        can_manage_official_agents: bool = False,
    ) -> ChatAgentResponse | None:
        agent = self.repository.publish(
            UUID(agent_id),
            UUID(user_id),
            can_manage_official_agents=can_manage_official_agents,
        )

        if not agent:
            return None

        record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not record:
            return None

        draft, access_role = record

        return _to_response(
            agent,
            access_role,
            include_system_prompt=True,
            draft_agent=draft,
        )


class ListChatAgentVersionsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str) -> list[dict]:
        return self.repository.list_versions(UUID(agent_id), UUID(user_id))


class ShareChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: ShareChatAgentRequest) -> bool:
        role = request.role or "viewer"

        if role not in ALLOWED_SHARE_ROLES:
            raise InvalidChatSessionInputError("Invalid share role")

        target_user_id = (request.target_user_id or "").strip()

        if not target_user_id:
            raise InvalidChatSessionInputError("targetUserId is required")

        if target_user_id == request.user_id:
            raise InvalidChatSessionInputError("Cannot share an agent with yourself")

        return self.repository.share(
            agent_id=UUID(request.agent_id),
            user_id=UUID(request.user_id),
            target_user_id=UUID(target_user_id),
            role=role,
        )


class UpsertChatAgentActionUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: UpsertChatAgentActionRequest) -> bool:
        sensitivity = request.sensitivity or "read"

        if sensitivity not in ALLOWED_SENSITIVITY:
            raise InvalidChatSessionInputError("Invalid action sensitivity")

        return self.repository.upsert_action(
            agent_id=UUID(request.agent_id),
            user_id=UUID(request.user_id),
            provider_key=_normalize_text(request.provider_key, 120, required=True),
            action_id=_normalize_text(request.action_id, 300, required=True),
            sensitivity=sensitivity,
            requires_confirmation=request.requires_confirmation,
            enabled=request.enabled,
            can_manage_official_agents=getattr(request, "can_manage_official_agents", False),
        )


class ListChatAgentActionsUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str) -> list[dict]:
        return self.repository.list_actions(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
        )


class ListChatAgentActionProvidersUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str) -> list[dict]:
        return self.repository.list_action_providers(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
        )


class UpsertChatAgentActionProviderUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        provider_key: str,
        enabled: bool = True,
        allow_read: bool = True,
        allow_write: bool = False,
        allow_admin: bool = False,
        requires_confirmation_for_write: bool = True,
        can_manage_official_agents: bool = False,
    ) -> bool:
        return self.repository.upsert_action_provider(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
            provider_key=_normalize_text(provider_key, 120, required=True),
            enabled=enabled,
            allow_read=allow_read,
            allow_write=allow_write,
            allow_admin=allow_admin,
            requires_confirmation_for_write=requires_confirmation_for_write,
            can_manage_official_agents=can_manage_official_agents,
        )


class DeleteChatAgentActionProviderUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        provider_key: str,
        can_manage_official_agents: bool = False,
    ) -> bool:
        return self.repository.delete_action_provider(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
            provider_key=_normalize_text(provider_key, 120, required=True),
            can_manage_official_agents=can_manage_official_agents,
        )


class DeleteChatAgentActionUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        agent_id: str,
        provider_key: str,
        action_id: str,
        can_manage_official_agents: bool = False,
    ) -> bool:
        return self.repository.delete_action(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
            provider_key=_normalize_text(provider_key, 120, required=True),
            action_id=_normalize_text(action_id, 300, required=True),
            can_manage_official_agents=can_manage_official_agents,
        )


def _sanitize_export_providers(providers: list[dict]) -> list[dict]:
    sanitized: list[dict] = []

    for item in providers:
        provider_key = str(item.get("providerKey") or "").strip()

        if not provider_key:
            continue

        sanitized.append(
            {
                "providerKey": provider_key,
                "enabled": bool(item.get("enabled", True)),
                "allowRead": bool(item.get("allowRead", True)),
                "allowWrite": bool(item.get("allowWrite", False)),
                "allowAdmin": bool(item.get("allowAdmin", False)),
                "requiresConfirmationForWrite": bool(
                    item.get("requiresConfirmationForWrite", True)
                ),
            }
        )

    return sanitized


def _sanitize_export_actions(actions: list[dict]) -> list[dict]:
    sanitized: list[dict] = []

    for item in actions:
        provider_key = str(item.get("providerKey") or "").strip()
        action_id = str(item.get("actionId") or "").strip()
        sensitivity = str(item.get("sensitivity") or "read")

        if not provider_key or not action_id:
            continue

        if sensitivity not in ALLOWED_SENSITIVITY:
            sensitivity = "read"

        sanitized.append(
            {
                "providerKey": provider_key,
                "actionId": action_id,
                "enabled": bool(item.get("enabled", True)),
                "sensitivity": sensitivity,
                "requiresConfirmation": bool(item.get("requiresConfirmation", False)),
            }
        )

    return sanitized


class ExportChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, *, user_id: str, agent_id: str) -> dict | None:
        record = self.repository.get_accessible_by_id(UUID(agent_id), UUID(user_id))

        if not record:
            return None

        agent, access_role = record

        if access_role not in {"owner", "editor", "system"}:
            raise ChatAgentPermissionDeniedError(
                "You do not have permission to export this agent"
            )

        providers = self.repository.list_action_providers(UUID(agent_id), UUID(user_id))
        actions = self.repository.list_actions(UUID(agent_id), UUID(user_id))

        metadata = dict(agent.metadata or {})

        return {
            "exportVersion": AGENT_EXPORT_VERSION,
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "suggestedKey": agent.key,
            "agent": {
                "name": agent.name,
                "description": agent.description,
                "systemPrompt": agent.system_prompt if _can_view_system_prompt(access_role) else None,
                "category": agent.category,
                "icon": agent.icon,
                "responseStyle": agent.response_style,
                "visibility": agent.visibility,
                "enabled": agent.enabled,
                "maxToolCalls": agent.max_tool_calls,
                "requiresConfirmationForWrite": agent.requires_confirmation_for_write,
                "metadata": metadata,
            },
            "actionProviders": _sanitize_export_providers(providers),
            "actions": _sanitize_export_actions(actions),
        }


class ImportChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        user_id: str,
        payload: dict,
        can_manage_official_agents: bool = False,
    ) -> ChatAgentResponse:
        export_payload = payload.get("export") if isinstance(payload.get("export"), dict) else payload

        if not isinstance(export_payload, dict):
            raise InvalidChatSessionInputError("export payload is required")

        version = int(export_payload.get("exportVersion") or 0)

        if version != AGENT_EXPORT_VERSION:
            raise InvalidChatSessionInputError("Unsupported export version")

        agent_data = export_payload.get("agent")

        if not isinstance(agent_data, dict):
            raise InvalidChatSessionInputError("export.agent is required")

        name = _normalize_text(
            payload.get("name") or agent_data.get("name"),
            120,
            required=True,
        )
        visibility = str(payload.get("visibility") or agent_data.get("visibility") or "private")

        if visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid agent visibility")

        if visibility == "system" and not can_manage_official_agents:
            visibility = "private"

        key_source = payload.get("key") or export_payload.get("suggestedKey") or name
        key = _slugify(str(key_source))
        owner_user_id = None if visibility == "system" else UUID(user_id)

        try:
            agent = self.repository.create(
                owner_user_id=owner_user_id,
                key=key,
                name=name,
                description=_normalize_text(agent_data.get("description"), 800),
                system_prompt=_normalize_text(agent_data.get("systemPrompt"), 12000),
                visibility=visibility,
                category=_normalize_text(agent_data.get("category"), 80),
                icon=_normalize_text(agent_data.get("icon"), 60),
                response_style=_normalize_text(agent_data.get("responseStyle"), 40),
                metadata=agent_data.get("metadata")
                if isinstance(agent_data.get("metadata"), dict)
                else None,
                max_tool_calls=agent_data.get("maxToolCalls"),
                requires_confirmation_for_write=agent_data.get("requiresConfirmationForWrite"),
                enabled=agent_data.get("enabled"),
            )
        except IntegrityError as exc:
            raise ChatAgentKeyConflictError("Agent key already exists") from exc

        apply_actions = bool(payload.get("applyActions", True))

        if apply_actions:
            providers = export_payload.get("actionProviders")
            actions = export_payload.get("actions")

            if isinstance(providers, list) or isinstance(actions, list):
                self.repository.apply_exported_action_configuration(
                    agent.id,
                    _sanitize_export_providers(providers if isinstance(providers, list) else []),
                    _sanitize_export_actions(actions if isinstance(actions, list) else []),
                )

        return _to_response(agent, "owner", include_system_prompt=True)
