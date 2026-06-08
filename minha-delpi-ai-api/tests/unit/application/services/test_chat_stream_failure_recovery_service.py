from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from app.application.services.chat_stream_failure_recovery_service import (
    ChatStreamFailureRecoveryService,
)
from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort


def _message(*, role: str, delivery_status: str, content: str = "") -> ChatMessage:
    return ChatMessage(
        id=uuid4(),
        session_id=uuid4(),
        role=role,
        content=content,
        metadata={"delivery": {"status": delivery_status}},
        created_at=datetime.now(timezone.utc),
        parent_message_id=None,
    )


def test_recovers_generating_assistant_placeholder():
    repository = Mock(spec=ChatSessionRepositoryPort)
    session_id = uuid4()
    user_id = uuid4()
    assistant = _message(role="assistant", delivery_status="generating")

    repository.get_session_by_id.return_value = ChatSession(
        id=session_id,
        user_id=user_id,
        title="Teste",
        context="geral",
        project_id=None,
        agent_id=None,
        is_pinned=False,
        active_leaf_message_id=assistant.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.list_messages_by_session.return_value = [
        _message(role="user", delivery_status="processing", content="oi"),
        assistant,
    ]

    ChatStreamFailureRecoveryService.recover(
        chat_repository=repository,
        session_id=session_id,
        detail="boom",
    )

    repository.update_assistant_message.assert_called_once()
    args = repository.update_assistant_message.call_args[0]
    assert args[0] == assistant.id
    assert "Não foi possível" in args[1]


def test_recovers_in_flight_user_message():
    repository = Mock(spec=ChatSessionRepositoryPort)
    session_id = uuid4()
    user_id = uuid4()
    user = _message(role="user", delivery_status="submitted", content="pergunta")

    repository.get_session_by_id.return_value = ChatSession(
        id=session_id,
        user_id=user_id,
        title="Teste",
        context="geral",
        project_id=None,
        agent_id=None,
        is_pinned=False,
        active_leaf_message_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repository.list_messages_by_session.return_value = [user]

    ChatStreamFailureRecoveryService.recover(
        chat_repository=repository,
        session_id=session_id,
        detail="timeout",
    )

    repository.update_user_message.assert_called_once()
    metadata_patch = repository.update_user_message.call_args.kwargs["metadata_patch"]
    assert metadata_patch["delivery"]["status"] == "cancelled"
