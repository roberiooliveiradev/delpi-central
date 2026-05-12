from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class CreateChatSessionUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, request: CreateChatSessionRequest) -> ChatSessionResponse:
        title = self._normalize_optional_text(request.title, max_length=150)
        context = self._normalize_optional_text(request.context, max_length=50)

        session = self.repository.create_session(
            user_id=UUID(request.user_id),
            title=title,
            context=context,
        )

        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            context=session.context,
            is_pinned=session.is_pinned,
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
            raise InvalidChatSessionInputError(
                f"Field exceeds maximum length of {max_length} characters"
            )

        return normalized
