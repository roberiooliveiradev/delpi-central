from uuid import UUID

from app.application.dto.chat_message_response import ChatMessageResponse
from app.application.dto.switch_chat_branch_request import SwitchChatBranchRequest
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_message_branch_service import ChatMessageBranchService


class SwitchChatBranchUseCase:
    def __init__(
        self,
        repository: ChatSessionRepositoryPort,
        history_use_case: GetChatHistoryUseCase | None = None,
    ):
        self.repository = repository
        self.history_use_case = history_use_case or GetChatHistoryUseCase(repository)

    def execute(self, request: SwitchChatBranchRequest) -> list[ChatMessageResponse]:
        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)
        anchor_user_message_id = UUID(request.anchor_user_message_id)

        session = self.repository.get_session_by_id(session_id)

        if not session:
            raise ChatSessionNotFoundError()

        if session.user_id != user_id:
            raise ChatSessionAccessDeniedError()

        anchor = self.repository.get_user_message_for_user(
            message_id=anchor_user_message_id,
            user_id=user_id,
            session_id=session_id,
        )

        if not anchor:
            raise ChatMessageNotFoundError()

        all_messages = self.repository.list_all_messages_by_session(session_id)
        leaf_id = ChatMessageBranchService.resolve_branch_leaf_id(
            all_messages,
            anchor_user_message_id,
        )

        if leaf_id is None:
            raise ChatMessageNotFoundError()

        updated = self.repository.set_active_leaf_message_id(
            session_id=session_id,
            user_id=user_id,
            message_id=leaf_id,
        )

        if not updated:
            raise ChatSessionNotFoundError()

        return self.history_use_case.execute(request.user_id, request.session_id)
