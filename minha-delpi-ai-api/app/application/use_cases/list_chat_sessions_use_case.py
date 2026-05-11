from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class ListChatSessionsUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str) -> list[ChatSessionResponse]:
        sessions = self.repository.list_sessions_by_user(UUID(user_id))

        return [
            ChatSessionResponse(
                id=str(session.id),
                title=session.title,
                context=session.context,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
            )
            for session in sessions
        ]
