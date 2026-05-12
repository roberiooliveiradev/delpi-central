from uuid import UUID

from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class DeleteChatSessionUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, user_id: str, session_id: str) -> bool:
        return self.repository.delete_session(
            session_id=UUID(session_id),
            user_id=UUID(user_id),
        )
