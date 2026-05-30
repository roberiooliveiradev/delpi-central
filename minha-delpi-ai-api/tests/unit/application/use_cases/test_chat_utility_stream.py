"""Perguntas utilitárias (hora/data) respondem direto, sem LLM."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession

FAKE_AGENT_ID = UUID("11111111-1111-4111-8111-111111111111")


def _session(*, agent_id: UUID | None = FAKE_AGENT_ID) -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title="Nova conversa",
        context=None,
        created_at=now,
        updated_at=now,
        agent_id=agent_id,
    )


def _build_stream_use_case(*, session: ChatSession):
    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_messages_by_session.return_value = []
    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
    chat_repository.create_message.side_effect = [user_message, assistant_message]

    workspace_context_service = MagicMock()
    workspace_context_service.build_context.return_value = {
        "project": None,
        "agent": {
            "id": str(FAKE_AGENT_ID),
            "name": "Agente Minha DELPI",
            "description": "assistente geral.",
        },
        "projectPrompt": None,
        "agentPrompt": "Você é o assistente.",
        "agentId": "11111111-1111-4111-8111-111111111111",
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
        "context": "doc",
        "sources": [{"title": "Doc"}],
    }

    prompt_policy_service = MagicMock()
    prompt_policy_service.build_contextual_prompt.return_value = "system"
    prompt_policy_service._load_policy.return_value = ""
    prompt_policy_service.build_active_skill_policy_sections.return_value = []

    message_security_service = MagicMock()
    message_security_service.secure_message.side_effect = lambda message, **_: message

    agentic_service = MagicMock()
    agentic_service.extend_tool_context.side_effect = lambda **kwargs: kwargs["tool_context"]

    return (
        StreamChatMessageUseCase(
            chat_repository=chat_repository,
            audit_repository=MagicMock(),
            message_security_service=message_security_service,
            llm_gateway=llm_gateway,
            prompt_policy_service=prompt_policy_service,
            rag_context_service=rag_context_service,
            chat_tool_context_service=chat_tool_context_service,
            workspace_context_service=workspace_context_service,
            chat_agentic_tool_loop_service=agentic_service,
        ),
        llm_gateway,
        rag_context_service,
        agentic_service,
    )


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.stream_chat_message_use_case",
        "app.domain.services.chat_external_action_direct_response_service",
    ):
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_ENABLED", True)
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_MAX_CHARS", 30)
        monkeypatch.setattr(f"{module}.Settings.CHAT_UTILITY_DIRECT_ENABLED", True)
        monkeypatch.setattr(
            f"{module}.Settings.CHAT_UTILITY_TIMEZONE", "America/Sao_Paulo"
        )
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
        monkeypatch.setattr(f"{module}.Settings.CHAT_AGENTIC_LOOP_ENABLED", True)


@pytest.fixture(autouse=True)
def patch_llm_cost(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.stream_chat_message_use_case.StreamChatMessageUseCase._estimate_cost",
        lambda self, **kwargs: None,
    )


def test_stream_current_time_uses_direct_answer_without_llm_or_rag_or_agentic():
    session = _session()
    stream_use_case, llm_gateway, rag_context_service, agentic_service = _build_stream_use_case(
        session=session
    )
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="que horas são?",
        access_token="token",
    )

    events = list(stream_use_case.stream(request))
    done = next(event for event in events if event.get("type") == "done")

    assert "Brasília" in done["answer"]
    assert ":" in done["answer"]
    llm_gateway.stream.assert_not_called()
    llm_gateway.generate.assert_not_called()
    rag_context_service.build_context.assert_not_called()
    agentic_service.extend_tool_context.assert_not_called()
