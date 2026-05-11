from dataclasses import dataclass
from uuid import UUID

from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


@dataclass(frozen=True)
class RenameChatSessionRequest:
    user_id: str
    session_id: str
    title: str


class RenameChatSessionUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, request: RenameChatSessionRequest):
        title = request.title.strip()

        if not title:
            raise ValueError("title is required")

        if len(title) > 120:
            raise ValueError("title must be at most 120 characters")

        return self.repository.rename_session(
            session_id=UUID(request.session_id),
            user_id=UUID(request.user_id),
            title=title,
        )
