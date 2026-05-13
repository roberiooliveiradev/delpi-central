from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class CreateChatSessionUseCase:
    def __init__(
        self,
        repository: ChatSessionRepositoryPort,
        project_repository: ChatProjectRepositoryPort | None = None,
        agent_repository: ChatAgentRepositoryPort | None = None,
    ):
        self.repository = repository
        self.project_repository = project_repository
        self.agent_repository = agent_repository

    def execute(self, request: CreateChatSessionRequest) -> ChatSessionResponse:
        user_id = UUID(request.user_id)
        title = self._normalize_optional_text(request.title, max_length=150)
        context = self._normalize_optional_text(request.context, max_length=50)
        project_id = UUID(request.project_id) if request.project_id else None
        agent_key = self._normalize_optional_text(request.agent_key, max_length=80)

        if project_id and self.project_repository:
            project_result = self.project_repository.get_accessible_by_id(
                project_id=project_id,
                user_id=user_id,
            )

            if not project_result:
                raise ValueError("Project not found or inaccessible")

            project, _role = project_result

            if not agent_key:
                agent_key = project.default_agent_key

        if agent_key and self.agent_repository:
            agent = self.agent_repository.get_enabled_by_key(agent_key, user_id=user_id)

            if not agent:
                raise ValueError("Agent not found or inaccessible")

        session = self.repository.create_session(
            user_id=user_id,
            title=title,
            context=context,
            project_id=project_id,
            agent_key=agent_key,
        )

        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            context=session.context,
            project_id=str(session.project_id) if session.project_id else None,
            agent_key=session.agent_key,
            is_pinned=bool(session.is_pinned),
            pinned_at=session.pinned_at.isoformat() if session.pinned_at else None,
            archived_at=session.archived_at.isoformat() if session.archived_at else None,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    def _normalize_optional_text(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        if len(normalized) > max_length:
            raise ValueError("Value exceeds maximum length")

        return normalized
