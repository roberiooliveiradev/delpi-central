"""Perguntas de identidade do assistente usam resposta canônica direta (sem LLM)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession

_IDENTITY_PHRASES = (
    "quem é vc?",
    "quem te criou?",
    "o que vc é?",
    "o que vc faz?",
    "como te usar",
)


def _session(*, agent_key: str | None = None) -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title=None,
        context=None,
        created_at=now,
        updated_at=now,
        agent_key=agent_key,
    )


def _workspace(*, common: bool) -> dict:
    if common:
        return {
            "project": None,
            "agent": None,
            "projectPrompt": None,
            "agentPrompt": None,
            "agentKey": None,
            "allowedActionIds": [],
            "capabilities": {},
            "specialization": None,
            "skills": {"companyKnowledge": True},
        }

    return {
        "project": None,
        "agent": {
            "key": "produtos",
            "name": "Especialista em Produtos",
            "description": "consultas e cadastro de produtos.",
        },
        "projectPrompt": None,
        "agentPrompt": "Você é especialista em produtos.",
        "agentKey": "produtos",
        "allowedActionIds": [],
        "capabilities": {},
        "specialization": None,
        "skills": {"companyKnowledge": True},
    }


def _build_use_cases(*, common: bool):
    session = _session(agent_key=None if common else "produtos")
    workspace = _workspace(common=common)

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_messages_by_session.return_value = []
    user_message = MagicMock()
    user_message.id = uuid4()
    chat_repository.create_message.return_value = user_message
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
    chat_repository.create_message.side_effect = [user_message, assistant_message]

    workspace_context_service = MagicMock()
    workspace_context_service.build_context.return_value = workspace

    llm_answer = "Resposta com base na documentação autorizada."
    llm_gateway = MagicMock()
    llm_gateway.generate.return_value = llm_answer
    llm_gateway.stream.return_value = iter([llm_answer])

    tool_context = {"context": "", "toolCalls": [], "nativeToolCalling": {}}
    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = tool_context

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {
        "context": "O assistente foi descrito no Arquiteto do Código.",
        "sources": [{"title": "O Arquiteto do Código"}],
    }

    prompt_policy_service = MagicMock()
    prompt_policy_service.build_contextual_prompt.return_value = "system"
    prompt_policy_service._load_policy.return_value = ""
    prompt_policy_service.build_active_skill_policy_sections.return_value = []

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

    return (
        session,
        SendChatMessageUseCase(**kwargs),
        StreamChatMessageUseCase(**kwargs),
        rag_context_service,
        llm_gateway,
    )


def _collect_stream_answer(events: list[dict]) -> str:
    streamed = "".join(
        event.get("content", "")
        for event in events
        if event.get("type") == "token"
    )
    if streamed:
        return streamed

    for event in reversed(events):
        if event.get("type") in {"playback", "done"}:
            answer = event.get("answer")
            if isinstance(answer, str) and answer.strip():
                return answer

    return streamed


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.send_chat_message_use_case",
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


@pytest.fixture(autouse=True)
def patch_llm_cost(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.send_chat_message_use_case.SendChatMessageUseCase._estimate_cost",
        lambda self, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.application.use_cases.stream_chat_message_use_case.StreamChatMessageUseCase._estimate_cost",
        lambda self, **kwargs: None,
    )


@pytest.mark.parametrize("message", _IDENTITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_identity_uses_direct_answer_without_llm(message: str, common: bool):
    session, send_use_case, _, rag_context_service, llm_gateway = _build_use_cases(
        common=common
    )
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    response = send_use_case.execute(request)

    llm_gateway.generate.assert_not_called()
    assert response.answer
    assert len(response.answer.strip()) > 40
    assert "2019" not in response.answer
    assert "openai" not in response.answer.lower()
    if message in {"quem te criou?", "quem é vc?", "quem é você?"}:
        rag_context_service.build_context.assert_not_called()


@pytest.mark.parametrize("message", ("quem te criou?", "quem é vc?"))
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_stream_identity_uses_direct_answer_without_llm(message: str, common: bool):
    session, _, stream_use_case, rag_context_service, llm_gateway = _build_use_cases(
        common=common
    )
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    llm_gateway.stream.assert_not_called()
    assert answer
    assert len(answer.strip()) > 40
    assert "2019" not in answer
    assert "openai" not in answer.lower()
    if message in {"quem te criou?", "quem é vc?"}:
        rag_context_service.build_context.assert_not_called()
