from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_stream_session_title_service import (
    ChatStreamSessionTitleService,
)
from app.domain.entities.chat_session import ChatSession


def _session(*, title: str | None = "Nova conversa") -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title=title,
        context=None,
        created_at=now,
        updated_at=now,
        agent_id=None,
    )


def test_should_generate_on_empty_session_title():
    service = ChatStreamSessionTitleService()
    session = _session(title="")

    assert service.should_generate(session, [], resend_from_message_id=None)


def test_should_not_generate_when_history_exists():
    service = ChatStreamSessionTitleService()
    session = _session(title="Nova conversa")

    assert not service.should_generate(session, [MagicMock()], resend_from_message_id=None)


def test_fallback_from_message_truncates_long_text():
    service = ChatStreamSessionTitleService()
    message = "x" * 60

    title = service.fallback_from_message(message)

    assert title.endswith("...")
    assert len(title) <= 51
