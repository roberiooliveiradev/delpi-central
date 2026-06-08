"""Título automático da sessão no primeiro turno do stream."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
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


def _build_stream_use_case(*, session: ChatSession):
    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_all_messages_by_session.return_value = []
    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
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
    llm_gateway.generate.return_value = "Resposta genérica."
    llm_gateway.stream.return_value = iter(["Resposta genérica."])

    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = {
        "context": "",
        "toolCalls": [],
        "nativeToolCalling": {},
    }

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "",
        "sources": [],
    }

    prompt_policy_service = MagicMock()
    prompt_policy_service.build_contextual_prompt.return_value = "system"
    prompt_policy_service._load_policy.return_value = ""
    prompt_policy_service.build_active_skill_policy_sections.return_value = []

    message_security_service = MagicMock()
    message_security_service.secure_message.side_effect = lambda message, **_: message

    return StreamChatMessageUseCase(
        chat_repository=chat_repository,
        audit_repository=MagicMock(),
        message_security_service=message_security_service,
        llm_gateway=llm_gateway,
        prompt_policy_service=prompt_policy_service,
        rag_context_service=rag_context_service,
        chat_tool_context_service=chat_tool_context_service,
        workspace_context_service=workspace_context_service,
    ), chat_repository


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.stream_chat_message_use_case",
        "app.domain.services.chat_external_action_direct_response_service",
    ):
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_ENABLED", False)
        monkeypatch.setattr(f"{module}.Settings.CHAT_HISTORY_MAX_MESSAGES", 12)
        monkeypatch.setattr(f"{module}.Settings.LLM_PROVIDER", "ollama")
        monkeypatch.setattr(f"{module}.Settings.OLLAMA_MODEL", "test-model")
        monkeypatch.setattr(
            f"{module}.Settings.CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS", 0
        )
        monkeypatch.setattr(
            f"{module}.Settings.CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS", 2000
        )
        monkeypatch.setattr(f"{module}.Settings.CHAT_PERSIST_BEFORE_PLAYBACK", False)
        monkeypatch.setattr(f"{module}.Settings.CHAT_SESSION_TITLE_LLM_ENABLED", False)


@pytest.fixture(autouse=True)
def patch_llm_cost(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
    )


def test_stream_renames_session_on_first_message():
    session = _session(title="Nova conversa")
    stream_use_case, chat_repository = _build_stream_use_case(session=session)
    message = "roteiro do 90260123"
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))

    assert any(event.get("type") == "done" for event in events)
    chat_repository.rename_session.assert_called_once_with(
        session_id=session.id,
        user_id=session.user_id,
        title=message,
    )


def test_stream_skips_rename_when_session_already_has_messages():
    session = _session(title="Nova conversa")
    stream_use_case, chat_repository = _build_stream_use_case(session=session)
    chat_repository.list_all_messages_by_session.return_value = [MagicMock()]
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="continuação",
        access_token=None,
    )

    list(stream_use_case.stream(request))

    chat_repository.rename_session.assert_not_called()
