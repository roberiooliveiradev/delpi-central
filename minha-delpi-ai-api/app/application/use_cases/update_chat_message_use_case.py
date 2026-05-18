from dataclasses import dataclass
from uuid import UUID

from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


@dataclass(frozen=True)
class UpdateChatMessageRequest:
    user_id: str
    message_id: str
    content: str


class UpdateChatMessageUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(self, request: UpdateChatMessageRequest):
        content = str(request.content or "").strip()

        if not content:
            raise ValueError("content is required")

        if len(content) > 8000:
            raise ValueError("content exceeds maximum length")

        metadata_patch = {"editMode": "manual"}

        return self.repository.update_user_message(
            message_id=UUID(request.message_id),
            user_id=UUID(request.user_id),
            content=content,
            metadata_patch=metadata_patch,
        )
