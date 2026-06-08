from uuid import UUID

from app.application.services.chat_stream_failure_recovery_service import (
    ChatStreamFailureRecoveryService,
)
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class CancelChatStreamUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, session_id: str) -> None:
        session = self.repository.get_session_by_id(UUID(session_id))

        if not session:
            raise ChatSessionNotFoundError()

        if str(session.user_id) != user_id:
            raise ChatSessionAccessDeniedError()

        ChatStreamFailureRecoveryService.recover(
            chat_repository=self.repository,
            session_id=session_id,
            detail="user_cancelled",
        )
