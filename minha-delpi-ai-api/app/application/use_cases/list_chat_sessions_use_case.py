from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


class ListChatSessionsUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(
        self,
        user_id: str,
        archived: bool = False,
    ) -> list[ChatSessionResponse]:
        sessions = self.repository.list_sessions_by_user(
            UUID(user_id),
            archived=archived,
        )

        return [
            ChatSessionResponse(
                id=str(session.id),
                title=session.title,
                context=session.context,
                project_id=str(session.project_id) if session.project_id else None,
                agent_id=str(session.agent_id) if session.agent_id else None,
                is_pinned=session.is_pinned,
                pinned_at=session.pinned_at.isoformat() if session.pinned_at else None,
                archived_at=session.archived_at.isoformat() if session.archived_at else None,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
            )
            for session in sessions
        ]
