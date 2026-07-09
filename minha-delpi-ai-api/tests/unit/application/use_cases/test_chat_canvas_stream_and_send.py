"""Garante fluxo de lousa (canvas) no chat base — stream + send, sem LLM."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_message import ChatMessage
from app.domain.entities.chat_session import ChatSession


def _session() -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title=None,
        context=None,
        created_at=now,
        updated_at=now,
        agent_id=None,
    )


def _assistant_history(session: ChatSession) -> list[ChatMessage]:
    now = datetime.now(timezone.utc)
    return [
        ChatMessage(
            id=uuid4(),
            session_id=session.id,
            role="assistant",
            content="## Perfil\n\nVocê é o analista João Silva.",
            metadata=None,
            created_at=now,
        )
    ]


def _build_use_cases():
    session = _session()
    workspace = {
        "project": None,
        "agent": None,
        "projectPrompt": None,
        "agentPrompt": None,
        "agentId": None,
        "allowedActionIds": [],
        "capabilities": {"canvas": True},
        "specialization": None,
    }

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    history = _assistant_history(session)
    chat_repository.list_messages_by_session.return_value = history
    chat_repository.list_all_messages_by_session.return_value = history

    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()

    chat_repository.create_message.side_effect = [user_message, assistant_message]
    chat_repository.update_assistant_message.return_value = assistant_message

    workspace_context_service = MagicMock()
    workspace_context_service.build_context.return_value = workspace

    llm_gateway = MagicMock()
    llm_gateway.generate.side_effect = AssertionError("LLM não deve ser chamado para lousa")
    llm_gateway.stream.side_effect = AssertionError("LLM stream não deve ser chamado para lousa")

    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.side_effect = AssertionError(
        "Tool context não deve ser montado para lousa"
    )

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {"context": "", "sources": []}

    prompt_policy_service = MagicMock()
    message_security_service = MagicMock()
    message_security_service.secure_message.side_effect = lambda message, **_: message

    kwargs = dict(
        chat_repository=chat_repository,
        audit_repository=MagicMock(),
        message_security_service=message_security_service,
        llm_gateway=llm_gateway,
        prompt_policy_service=prompt_policy_service,
        rag_context_service=rag_context_service,
        chat_tool_context_service=chat_tool_context_service,
        workspace_context_service=workspace_context_service,
    )

    return session, SendChatMessageUseCase(**kwargs), StreamChatMessageUseCase(**kwargs)


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.send_chat_message_use_case",
        "app.application.use_cases.stream_chat_message_use_case",
    ):
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_ENABLED", False)
        monkeypatch.setattr(f"{module}.Settings.CHAT_PERSIST_BEFORE_PLAYBACK", True)
        monkeypatch.setattr(f"{module}.Settings.LLM_PROVIDER", "ollama")
        monkeypatch.setattr(f"{module}.Settings.OLLAMA_MODEL", "test-model")


@pytest.fixture(autouse=True)
def patch_llm_cost(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
    )


@pytest.mark.parametrize("message", ("coloque na lousa", "coloque em canva"))
def test_send_canvas_open_without_llm(message: str):
    session, send_use_case, _ = _build_use_cases()
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    response = send_use_case.execute(request)

    assert response.canvasOpen is not None
    assert "João Silva" in response.canvasOpen["markdown"]
    assert "lousa" in response.answer.lower()


@pytest.mark.parametrize("message", ("coloque na lousa", "coloque em canva"))
def test_stream_canvas_open_without_llm(message: str):
    session, _, stream_use_case = _build_use_cases()
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    canvas_events = [event for event in events if event.get("type") == "canvas_open"]
    playback_events = [event for event in events if event.get("type") == "playback"]

    assert canvas_events
    assert "João Silva" in canvas_events[0].get("markdown", "")
    assert playback_events
    assert "lousa" in playback_events[0].get("answer", "").lower()
