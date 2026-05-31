from uuid import UUID

from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_memory_repository_port import ChatSessionMemoryRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class ClearChatSessionMemoryUseCase:
    def __init__(
        self,
        session_repository: ChatSessionRepositoryPort,
        memory_repository: ChatSessionMemoryRepositoryPort,
    ):
        self.session_repository = session_repository
        self.memory_repository = memory_repository

    def execute(self, *, user_id: UUID, session_id: UUID) -> int:
        session = self.session_repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError(str(session_id))

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError(str(session_id))

        return self.memory_repository.deactivate_all(session_id)
