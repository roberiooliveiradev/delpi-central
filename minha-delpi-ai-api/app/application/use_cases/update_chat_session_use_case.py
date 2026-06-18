from uuid import UUID

from app.application.dto.chat_session_response import ChatSessionResponse
from app.application.dto.update_chat_session_request import UpdateChatSessionRequest
from app.domain.ports.chat_project_repository_port import ChatProjectRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


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
        active_leaf_message_id=(
            str(session.active_leaf_message_id) if session.active_leaf_message_id else None
        ),
    )


class UpdateChatSessionUseCase:
    def __init__(
        self,
        repository: ChatSessionRepositoryPort,
        project_repository: ChatProjectRepositoryPort | None = None,
    ):
        self.repository = repository
        self.project_repository = project_repository

    def execute(self, request: UpdateChatSessionRequest) -> ChatSessionResponse | None:
        if not request.update_title and not request.update_project_id:
            raise ValueError("Informe title ou projectId para atualizar a sessão.")

        user_id = UUID(request.user_id)
        session_id = UUID(request.session_id)
        session = self.repository.get_session_by_id(session_id)

        if not session or session.user_id != user_id:
            return None

        if request.update_title:
            title = (request.title or "").strip()

            if not title:
                raise ValueError("title is required")

            if len(title) > 120:
                raise ValueError("title must be at most 120 characters")

            session = self.repository.rename_session(
                session_id=session_id,
                user_id=user_id,
                title=title,
            )

            if not session:
                return None

        if request.update_project_id:
            project_uuid = UUID(request.project_id) if request.project_id else None

            if project_uuid and self.project_repository:
                project_result = self.project_repository.get_accessible_by_id(
                    project_id=project_uuid,
                    user_id=user_id,
                )

                if not project_result:
                    raise ValueError("Project not found or inaccessible")

            updated = self.repository.update_session_project_id(
                session_id=session_id,
                user_id=user_id,
                project_id=project_uuid,
            )

            if not updated:
                return None

            session = self.repository.get_session_by_id(session_id)

            if not session:
                return None

        return _to_response(session)
