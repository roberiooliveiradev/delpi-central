import re
from uuid import UUID

from app.application.dto.chat_agent_response import ChatAgentResponse
from app.application.dto.create_chat_agent_request import CreateChatAgentRequest
from app.application.dto.share_chat_agent_request import ShareChatAgentRequest
from app.application.dto.update_chat_agent_request import UpdateChatAgentRequest
from app.application.dto.upsert_chat_agent_action_request import UpsertChatAgentActionRequest
from app.domain.entities.chat_agent import ChatAgent
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort


ALLOWED_VISIBILITY = {"private", "public"}
ALLOWED_SHARE_ROLES = {"viewer", "editor"}
ALLOWED_SENSITIVITY = {"read", "write", "admin"}


def _to_response(agent: ChatAgent, access_role: str = "viewer") -> ChatAgentResponse:
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

    def execute(self, user_id: str) -> list[ChatAgentResponse]:
        agents = self.repository.list_accessible(UUID(user_id))
        return [_to_response(agent, access_role) for agent, access_role in agents]


class CreateChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: CreateChatAgentRequest) -> ChatAgentResponse:
        name = _normalize_text(request.name, 120, required=True)
        visibility = request.visibility or "private"

        if visibility not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid agent visibility")

        key = _slugify(request.key or name)

        agent = self.repository.create(
            owner_user_id=UUID(request.user_id),
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

        return _to_response(agent, "owner")


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
        }

        if fields["visibility"] is not None and fields["visibility"] not in ALLOWED_VISIBILITY:
            raise InvalidChatSessionInputError("Invalid agent visibility")

        agent = self.repository.update(
            agent_id=UUID(request.agent_id),
            user_id=UUID(request.user_id),
            **fields,
        )

        if not agent:
            return None

        return _to_response(agent, "editor")


class DeleteChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, agent_id: str) -> bool:
        return self.repository.delete(
            agent_id=UUID(agent_id),
            user_id=UUID(user_id),
        )


class ShareChatAgentUseCase:
    def __init__(self, repository: ChatAgentRepositoryPort):
        self.repository = repository

    def execute(self, request: ShareChatAgentRequest) -> bool:
        role = request.role or "viewer"

        if role not in ALLOWED_SHARE_ROLES:
            raise InvalidChatSessionInputError("Invalid share role")

        return self.repository.share(
            agent_id=UUID(request.agent_id),
            user_id=UUID(request.user_id),
            target_user_id=UUID(request.target_user_id),
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
        )
