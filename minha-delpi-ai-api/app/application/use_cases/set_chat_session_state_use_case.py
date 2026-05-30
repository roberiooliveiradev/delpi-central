from dataclasses import dataclass
from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


@dataclass(frozen=True)
class SetChatSessionStateRequest:
    user_id: str
    session_id: str


def _to_response(session) -> ChatSessionResponse:
    return ChatSessionResponse(
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


class SetChatSessionPinnedUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(
        self,
        request: SetChatSessionStateRequest,
        pinned: bool,
    ) -> ChatSessionResponse | None:
        session = self.repository.set_session_pinned(
            session_id=UUID(request.session_id),
            user_id=UUID(request.user_id),
            pinned=pinned,
        )

        if not session:
            return None

        return _to_response(session)


class SetChatSessionArchivedUseCase:
    def __init__(self, repository: ChatSessionRepositoryPort):
        self.repository = repository

    def execute(
        self,
        request: SetChatSessionStateRequest,
        archived: bool,
    ) -> ChatSessionResponse | None:
        session = self.repository.set_session_archived(
            session_id=UUID(request.session_id),
            user_id=UUID(request.user_id),
            archived=archived,
        )

        if not session:
            return None

        return _to_response(session)
