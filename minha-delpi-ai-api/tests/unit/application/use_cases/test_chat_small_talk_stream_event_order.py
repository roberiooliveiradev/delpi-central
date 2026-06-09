"""Ordem dos eventos SSE em cumprimentos — status de direct answer antes de sources/tools."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession


def _session() -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Nova conversa",
        context=None,
        created_at=now,
        updated_at=now,
        agent_id=None,
    )


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.stream_chat_message_use_case",
        "app.application.services.chat_turn.chat_turn_completion_service",
    ):
        monkeypatch.setattr(f"{module}.Settings.CHAT_PERSIST_BEFORE_PLAYBACK", True)
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_ENABLED", True)
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_MAX_CHARS", 30)
        monkeypatch.setattr(f"{module}.Settings.CHAT_SESSION_TITLE_LLM_ENABLED", False)
        monkeypatch.setattr(f"{module}.Settings.CHAT_AGENTIC_LOOP_ENABLED", False)

    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
    )


def test_greeting_emits_direct_answer_status_before_sources(monkeypatch):
    session = _session()
    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_all_messages_by_session.return_value = []
    chat_repository.list_messages_by_session.return_value = []
    chat_repository.create_message.side_effect = [user_message, assistant_message]

    workspace_context_service = MagicMock()
    workspace_context_service.build_context.return_value = {
        "project": None,
        "agent": None,
        "projectPrompt": None,
        "agentPrompt": None,
        "agentId": None,
        "allowedActionIds": [],
        "capabilities": {},
        "specialization": None,
        "skills": {"companyKnowledge": True},
    }

    llm_gateway = MagicMock()
    llm_gateway.stream.return_value = iter(["Não deveria chamar LLM"])

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {"context": "", "sources": []}

    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = {
        "context": "",
        "toolCalls": [],
        "nativeToolCalling": {},
    }

    message_security_service = MagicMock()
    message_security_service.secure_message.side_effect = lambda message, **_: message

    use_case = StreamChatMessageUseCase(
        chat_repository=chat_repository,
        audit_repository=MagicMock(),
        message_security_service=message_security_service,
        llm_gateway=llm_gateway,
        prompt_policy_service=MagicMock(),
        rag_context_service=rag_context_service,
        chat_tool_context_service=chat_tool_context_service,
        workspace_context_service=workspace_context_service,
        chat_agentic_tool_loop_service=MagicMock(),
    )

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="ola",
        access_token="token",
    )

    events = list(use_case.stream(request))
    types = [event.get("type") for event in events]
    statuses = [
        event.get("message")
        for event in events
        if event.get("type") == "status" and isinstance(event.get("message"), str)
    ]

    assert types.index("status") < types.index("sources")
    assert any("pronta" in status.lower() for status in statuses)
    assert "token" not in types
    llm_gateway.stream.assert_not_called()
    rag_context_service.build_context.assert_not_called()
