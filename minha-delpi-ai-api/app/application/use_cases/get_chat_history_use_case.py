from uuid import UUID

from app.application.dto.chat_message_response import ChatMessageResponse
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_message_branch_service import ChatMessageBranchService
from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
    PostgresChatMessageFeedbackRepository,
)


class GetChatHistoryUseCase:
    def __init__(
        self,
        repository: ChatSessionRepositoryPort,
        feedback_repository: PostgresChatMessageFeedbackRepository | None = None,
    ):
        self.repository = repository
        self.feedback_repository = feedback_repository or PostgresChatMessageFeedbackRepository()

    def execute(self, user_id: str, session_id: str) -> list[ChatMessageResponse]:
        session = self.repository.get_session_by_id(UUID(session_id))

        if not session:
            raise ChatSessionNotFoundError()

        if str(session.user_id) != user_id:
            raise ChatSessionAccessDeniedError()

        all_messages = self.repository.list_all_messages_by_session(UUID(session_id))
        active_path = ChatMessageBranchService.build_active_path(
            all_messages,
            session.active_leaf_message_id,
        )
        branch_navigation = ChatMessageBranchService.build_user_branch_navigation(
            all_messages,
            active_path,
        )
        feedback_map = self.feedback_repository.list_feedback_by_message_ids(
            message_ids=[message.id for message in active_path],
            user_id=UUID(user_id),
        )

        return [
            ChatMessageResponse(
                id=str(message.id),
                session_id=str(message.session_id),
                role=message.role,
                content=message.content,
                metadata=message.metadata,
                created_at=message.created_at.isoformat(),
                parent_message_id=(
                    str(message.parent_message_id)
                    if message.parent_message_id
                    else None
                ),
                branch=branch_navigation.get(str(message.id)),
                user_feedback=(
                    feedback_map.get(str(message.id), {}).get("rating")
                    if message.role == "assistant"
                    else None
                ),
                user_feedback_reason=(
                    feedback_map.get(str(message.id), {}).get("reason")
                    if message.role == "assistant"
                    else None
                ),
            )
            for message in active_path
        ]
