from uuid import UUID

from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
    PostgresChatMessageFeedbackRepository,
)


class UpsertChatMessageFeedbackUseCase:
    def __init__(
        self,
        session_repository: ChatSessionRepositoryPort,
        feedback_repository: PostgresChatMessageFeedbackRepository | None = None,
    ):
        self.session_repository = session_repository
        self.feedback_repository = feedback_repository or PostgresChatMessageFeedbackRepository()

    def execute(
        self,
        *,
        user_id: str,
        session_id: str,
        message_id: str,
        rating: int | None,
    ) -> dict | None:
        session = self.session_repository.get_session_by_id(UUID(session_id))

        if not session:
            raise ChatSessionNotFoundError()

        if str(session.user_id) != user_id:
            raise ChatSessionAccessDeniedError()

        message_session_id = self.feedback_repository.get_message_session_id(UUID(message_id))

        if not message_session_id or str(message_session_id) != session_id:
            raise ValueError("message not found in session")

        assistant = self.feedback_repository.get_assistant_message(UUID(message_id))

        if not assistant:
            raise ValueError("feedback is only available for assistant messages")

        user_uuid = UUID(user_id)
        message_uuid = UUID(message_id)

        if rating is None:
            removed = self.feedback_repository.delete_feedback(
                message_id=message_uuid,
                user_id=user_uuid,
            )

            return {"removed": removed}

        if rating not in (-1, 1):
            raise ValueError("rating must be -1 or 1")

        return self.feedback_repository.upsert_feedback(
            message_id=message_uuid,
            user_id=user_uuid,
            rating=rating,
        )
