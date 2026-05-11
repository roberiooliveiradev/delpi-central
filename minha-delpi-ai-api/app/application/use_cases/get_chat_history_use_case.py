from uuid import UUID

from app.application.dto.chat_message_response import ChatMessageResponse
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class GetChatHistoryUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, session_id: str) -> list[ChatMessageResponse]:
        session = self.repository.get_session_by_id(UUID(session_id))

        if not session:
            raise ChatSessionNotFoundError()

        if str(session.user_id) != user_id:
            raise ChatSessionAccessDeniedError()

        messages = self.repository.list_messages_by_session(UUID(session_id))

        return [
            ChatMessageResponse(
                id=str(message.id),
                session_id=str(message.session_id),
                role=message.role,
                content=message.content,
                metadata=message.metadata,
                created_at=message.created_at.isoformat(),
            )
            for message in messages
        ]
