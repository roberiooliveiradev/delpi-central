from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
from app.domain.services.chat_message_delivery_service import ChatMessageDeliveryService


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
        if request.fork_from_session_id and request.fork_until_message_id:
            return self._fork_session(request)

        user_id = UUID(request.user_id)
        title = self._normalize_optional_text(request.title, max_length=150)
        context = self._normalize_optional_text(request.context, max_length=50)
        project_id = UUID(request.project_id) if request.project_id else None
        agent_id = self._parse_agent_id(request.agent_id)

        if project_id and self.project_repository:
            project_result = self.project_repository.get_accessible_by_id(
                project_id=project_id,
                user_id=user_id,
            )

            if not project_result:
                raise ValueError("Project not found or inaccessible")

            project, _role = project_result

        if agent_id and self.agent_repository:
            agent = self.agent_repository.get_enabled_by_id(agent_id, user_id=user_id)

            if not agent:
                raise ValueError("Agent not found or inaccessible")

        session = self.repository.create_session(
            user_id=user_id,
            title=title,
            context=context,
            project_id=project_id,
            agent_id=agent_id,
        )

        return self._to_response(session)

    def _fork_session(self, request: CreateChatSessionRequest) -> ChatSessionResponse:
        user_id = UUID(request.user_id)
        source_session_id = UUID(request.fork_from_session_id)
        until_message_id = UUID(request.fork_until_message_id)

        source_session = self.repository.get_session_by_id(source_session_id)

        if not source_session:
            raise ChatSessionNotFoundError()

        if source_session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        until_message = self.repository.get_message_by_id(
            until_message_id,
            user_id=user_id,
        )

        if not until_message or until_message.session_id != source_session_id:
            raise ChatMessageNotFoundError()

        all_messages = self.repository.list_all_messages_by_session(source_session_id)

        if request.fork_resend_user_message and until_message.role == "user":
            # Copia só o contexto anterior — a pergunta será reenviada uma vez pelo cliente.
            if until_message.parent_message_id:
                path_to_fork = ChatMessageBranchService.build_path_to_message(
                    all_messages,
                    until_message.parent_message_id,
                )
            else:
                path_to_fork = []
        else:
            path_to_fork = ChatMessageBranchService.build_fork_path(
                all_messages,
                until_message_id,
                source_session.active_leaf_message_id,
                include_assistant_reply=not request.fork_resend_user_message,
            )

            if not path_to_fork or path_to_fork[-1].id != until_message_id:
                raise ChatMessageNotFoundError()

        title = self._normalize_optional_text(request.title, max_length=150)
        if not title:
            source_title = (source_session.title or "Conversa").strip()
            title = f"{source_title} (continuação)"[:150]

        context = self._normalize_optional_text(request.context, max_length=50)
        if not context:
            context = source_session.context

        project_id = UUID(request.project_id) if request.project_id else source_session.project_id
        agent_id = self._parse_agent_id(request.agent_id) or source_session.agent_id

        if project_id and self.project_repository:
            project_result = self.project_repository.get_accessible_by_id(
                project_id=project_id,
                user_id=user_id,
            )

            if not project_result:
                raise ValueError("Project not found or inaccessible")

        if agent_id and self.agent_repository:
            agent = self.agent_repository.get_enabled_by_id(agent_id, user_id=user_id)

            if not agent:
                raise ValueError("Agent not found or inaccessible")

        new_session = self.repository.create_session(
            user_id=user_id,
            title=title,
            context=context,
            project_id=project_id,
            agent_id=agent_id,
        )

        previous_parent_id: UUID | None = None
        last_message_id: UUID | None = None

        for source_message in path_to_fork:
            metadata = dict(source_message.metadata or {})
            metadata["fork"] = {
                "fromSessionId": str(source_session_id),
                "fromMessageId": str(source_message.id),
            }

            if source_message.role in ("user", "assistant"):
                metadata = ChatMessageDeliveryService.ready_metadata(
                    metadata,
                    playback_pending=False,
                )

            copied = self.repository.create_message(
                session_id=new_session.id,
                role=source_message.role,
                content=source_message.content,
                metadata=metadata,
                parent_message_id=previous_parent_id,
            )
            previous_parent_id = copied.id
            last_message_id = copied.id

        if last_message_id is not None:
            self.repository.set_active_leaf_message_id(
                session_id=new_session.id,
                user_id=user_id,
                message_id=last_message_id,
            )
            new_session = self.repository.get_session_by_id(new_session.id) or new_session

        return self._to_response(new_session)

    def _to_response(self, session) -> ChatSessionResponse:
        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            context=session.context,
            project_id=str(session.project_id) if session.project_id else None,
            agent_id=str(session.agent_id) if session.agent_id else None,
            is_pinned=bool(session.is_pinned),
            pinned_at=session.pinned_at.isoformat() if session.pinned_at else None,
            archived_at=session.archived_at.isoformat() if session.archived_at else None,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            active_leaf_message_id=(
                str(session.active_leaf_message_id)
                if session.active_leaf_message_id
                else None
            ),
        )

    def _parse_agent_id(self, value: str | None) -> UUID | None:
        if not value:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return UUID(normalized)

    def _normalize_optional_text(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        if len(normalized) > max_length:
            raise ValueError("Value exceeds maximum length")

        return normalized
