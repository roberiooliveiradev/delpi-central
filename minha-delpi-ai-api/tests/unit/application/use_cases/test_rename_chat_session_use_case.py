from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.rename_chat_session_use_case import (
    RenameChatSessionRequest,
    RenameChatSessionUseCase,
)


@dataclass
class FakeSession:
    id: UUID
    user_id: UUID
    title: str
    context: str
    created_at: datetime
    updated_at: datetime


class FakeRepository:
    def __init__(self, session=None):
        self.session = session
        self.last_title = None

    def rename_session(self, session_id, user_id, title):
        self.last_title = title

        if self.session:
            self.session.title = title

        return self.session


def test_rename_chat_session_success():
    session = FakeSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Antes",
        context="geral",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository = FakeRepository(session=session)
    use_case = RenameChatSessionUseCase(repository)

    result = use_case.execute(
        RenameChatSessionRequest(
            user_id=str(session.user_id),
            session_id=str(session.id),
            title="  Depois  ",
        )
    )

    assert result is not None
    assert repository.last_title == "Depois"
    assert result.title == "Depois"


def test_rename_chat_session_requires_title():
    use_case = RenameChatSessionUseCase(FakeRepository())

    with pytest.raises(ValueError, match="title is required"):
        use_case.execute(
            RenameChatSessionRequest(
                user_id=str(uuid4()),
                session_id=str(uuid4()),
                title="   ",
            )
        )


def test_rename_chat_session_limits_title_length():
    use_case = RenameChatSessionUseCase(FakeRepository())

    with pytest.raises(ValueError, match="at most 120"):
        use_case.execute(
            RenameChatSessionRequest(
                user_id=str(uuid4()),
                session_id=str(uuid4()),
                title="x" * 121,
            )
        )


def test_rename_chat_session_not_found():
    use_case = RenameChatSessionUseCase(FakeRepository(session=None))

    result = use_case.execute(
        RenameChatSessionRequest(
            user_id=str(uuid4()),
            session_id=str(uuid4()),
            title="Título",
        )
    )

    assert result is None
