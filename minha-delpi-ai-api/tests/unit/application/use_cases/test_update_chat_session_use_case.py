from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.dto.update_chat_session_request import UpdateChatSessionRequest
from app.application.use_cases.update_chat_session_use_case import UpdateChatSessionUseCase


@dataclass
class FakeSession:
    id: UUID
    user_id: UUID
    title: str
    context: str | None
    project_id: UUID | None = None
    agent_id: UUID | None = None
    is_pinned: bool = False
    pinned_at: datetime | None = None
    archived_at: datetime | None = None
    active_leaf_message_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeSessionRepository:
    def __init__(self, session: FakeSession | None = None):
        self.session = session
        self.last_project_id: UUID | None | object = object()

    def get_session_by_id(self, session_id: UUID):
        if self.session and self.session.id == session_id:
            return self.session
        return None

    def rename_session(self, session_id: UUID, user_id: UUID, title: str):
        if not self.session or self.session.id != session_id or self.session.user_id != user_id:
            return None

        self.session.title = title
        return self.session

    def update_session_project_id(
        self,
        session_id: UUID,
        user_id: UUID,
        project_id: UUID | None,
    ) -> bool:
        if not self.session or self.session.id != session_id or self.session.user_id != user_id:
            return False

        self.last_project_id = project_id
        self.session.project_id = project_id
        return True


class FakeProjectRepository:
    def __init__(self, accessible: bool = True):
        self.accessible = accessible
        self.last_project_id: UUID | None = None

    def get_accessible_by_id(self, project_id: UUID, user_id: UUID):
        self.last_project_id = project_id

        if not self.accessible:
            return None

        return (object(), "owner")


def test_update_chat_session_moves_to_project():
    session = FakeSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Conversa",
        context="geral",
    )
    project_id = uuid4()
    repository = FakeSessionRepository(session=session)
    project_repository = FakeProjectRepository()
    use_case = UpdateChatSessionUseCase(repository, project_repository)

    result = use_case.execute(
        UpdateChatSessionRequest(
            user_id=str(session.user_id),
            session_id=str(session.id),
            project_id=str(project_id),
            update_project_id=True,
        )
    )

    assert result is not None
    assert result.project_id == str(project_id)
    assert repository.last_project_id == project_id


def test_update_chat_session_rejects_inaccessible_project():
    session = FakeSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Conversa",
        context="geral",
    )
    use_case = UpdateChatSessionUseCase(
        FakeSessionRepository(session=session),
        FakeProjectRepository(accessible=False),
    )

    with pytest.raises(ValueError, match="Project not found"):
        use_case.execute(
            UpdateChatSessionRequest(
                user_id=str(session.user_id),
                session_id=str(session.id),
                project_id=str(uuid4()),
                update_project_id=True,
            )
        )


def test_update_chat_session_still_renames_title():
    session = FakeSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Antes",
        context="geral",
    )
    use_case = UpdateChatSessionUseCase(FakeSessionRepository(session=session))

    result = use_case.execute(
        UpdateChatSessionRequest(
            user_id=str(session.user_id),
            session_id=str(session.id),
            title="Depois",
            update_title=True,
        )
    )

    assert result is not None
    assert result.title == "Depois"
