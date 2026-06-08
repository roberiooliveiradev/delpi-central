from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.use_cases.cancel_chat_stream_use_case import CancelChatStreamUseCase
from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


def _session(*, session_id, user_id) -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=session_id,
        user_id=user_id,
        title="Teste",
        context="geral",
        project_id=None,
        agent_id=None,
        is_pinned=False,
        active_leaf_message_id=None,
        created_at=now,
        updated_at=now,
    )


def test_cancel_chat_stream_marks_in_flight_messages():
    repository = Mock(spec=ChatSessionRepositoryPort)
    session_id = uuid4()
    user_id = uuid4()
    user_message = ChatMessage(
        id=uuid4(),
        session_id=session_id,
        role="user",
        content="pergunta",
        metadata={"delivery": {"status": "processing"}},
        created_at=datetime.now(timezone.utc),
        parent_message_id=None,
    )

    repository.get_session_by_id.return_value = _session(
        session_id=session_id,
        user_id=user_id,
    )
    repository.list_messages_by_session.return_value = [user_message]

    CancelChatStreamUseCase(repository).execute(str(user_id), str(session_id))

    repository.update_user_message.assert_called_once()


def test_cancel_chat_stream_rejects_foreign_session():
    repository = Mock(spec=ChatSessionRepositoryPort)
    session_id = uuid4()
    owner_id = uuid4()

    repository.get_session_by_id.return_value = _session(
        session_id=session_id,
        user_id=owner_id,
    )

    with pytest.raises(ChatSessionAccessDeniedError):
        CancelChatStreamUseCase(repository).execute(str(uuid4()), str(session_id))


def test_cancel_chat_stream_not_found():
    repository = Mock(spec=ChatSessionRepositoryPort)
    repository.get_session_by_id.return_value = None

    with pytest.raises(ChatSessionNotFoundError):
        CancelChatStreamUseCase(repository).execute(str(uuid4()), str(uuid4()))
