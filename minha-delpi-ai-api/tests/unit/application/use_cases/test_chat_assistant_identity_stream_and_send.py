"""Perguntas de identidade: síntese meta LLM com fatos canônicos (sem RAG)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession

FAKE_AGENT_ID = UUID("11111111-1111-4111-8111-111111111111")

_IDENTITY_META_LLM_PHRASES = (
    "quem é vc?",
    "quem te criou?",
    "o que vc é?",
    "como te usar",
)

_IDENTITY_DIRECT_CAPABILITY_PHRASES = ("o que vc faz?",)

_IDENTITY_ONLY_NO_RAG = frozenset({"quem te criou?", "quem é vc?"})

_META_SYNTHESIS_MARKER = "fatos canônicos"


def _session(*, agent_id: UUID | None = None) -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        user_id=uuid4(),
        title=None,
        context=None,
        created_at=now,
        updated_at=now,
        agent_id=agent_id,
    )


def _workspace(*, common: bool) -> dict:
    if common:
        return {
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

    return {
        "project": None,
        "agent": {
            "id": str(FAKE_AGENT_ID),
            "name": "Especialista em Produtos",
            "description": "consultas e cadastro de produtos.",
        },
        "projectPrompt": None,
        "agentPrompt": "Você é especialista em produtos.",
        "agentId": "11111111-1111-4111-8111-111111111111",
        "allowedActionIds": [],
        "capabilities": {},
        "specialization": None,
        "skills": {"companyKnowledge": True},
    }


def _build_use_cases(*, common: bool):
    session = _session(agent_id=None if common else FAKE_AGENT_ID)
    workspace = _workspace(common=common)

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_messages_by_session.return_value = []
    chat_repository.list_all_messages_by_session.return_value = []
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


def _assert_meta_synthesis_llm_messages(messages: list[dict], *, question: str) -> None:
    user_messages = [item for item in messages if item.get("role") == "user"]
    assert user_messages
    content = user_messages[-1]["content"]
    assert _META_SYNTHESIS_MARKER in content
    assert question in content


from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime


@pytest.fixture(autouse=True)
def patch_intelligence_runtime(monkeypatch):
    patch_resolve_chat_intelligence_runtime(monkeypatch)


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "CHAT_FAST_PATH_ENABLED", False)
    monkeypatch.setattr(Settings, "CHAT_HISTORY_MAX_MESSAGES", 12)
    monkeypatch.setattr(Settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(Settings, "OLLAMA_MODEL", "test-model")
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS", 0)
    monkeypatch.setattr(Settings, "CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS", 2000)
    monkeypatch.setattr(Settings, "CHAT_PERSIST_BEFORE_PLAYBACK", False)


@pytest.fixture(autouse=True)
def patch_llm_cost(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
    )


@pytest.mark.parametrize("message", _IDENTITY_META_LLM_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_identity_uses_meta_synthesis_without_rag(message: str, common: bool):
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

    llm_gateway.generate.assert_called_once()
    _assert_meta_synthesis_llm_messages(
        llm_gateway.generate.call_args[0][0],
        question=message,
    )
    assert response.answer
    assert len(response.answer.strip()) > 10
    assert "2019" not in response.answer
    assert "openai" not in response.answer.lower()
    if message in _IDENTITY_ONLY_NO_RAG:
        rag_context_service.build_context.assert_not_called()


@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_capabilities_inquiry_uses_direct_answer_without_llm(common: bool):
    session, send_use_case, _, rag_context_service, llm_gateway = _build_use_cases(
        common=common
    )
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="o que vc faz?",
        access_token=None,
    )

    response = send_use_case.execute(request)

    llm_gateway.generate.assert_not_called()
    assert response.answer
    assert len(response.answer.strip()) > 10
    rag_context_service.build_context.assert_not_called()


@pytest.mark.parametrize("message", ("quem te criou?", "quem é vc?"))
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_stream_identity_uses_meta_synthesis_without_rag(message: str, common: bool):
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

    llm_gateway.stream.assert_called_once()
    _assert_meta_synthesis_llm_messages(
        llm_gateway.stream.call_args[0][0],
        question=message,
    )
    assert answer
    assert len(answer.strip()) > 10
    assert "2019" not in answer
    assert "openai" not in answer.lower()
    rag_context_service.build_context.assert_not_called()
