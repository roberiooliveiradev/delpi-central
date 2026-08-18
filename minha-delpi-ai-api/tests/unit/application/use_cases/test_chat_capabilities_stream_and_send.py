"""Garante síntese LLM de capacidades no chat comum e com agente (stream + send)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession
from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime

_CAPABILITY_PHRASES = (
    "o que vc é capaz de fazer?",
    "ajuda",
    "o que você pode fazer?",
)

FAKE_AGENT_ID = UUID("11111111-1111-4111-8111-111111111111")
_LLM_ANSWER = "Posso ajudar com documentação autorizada e, com um agente, consultas operacionais."


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
        }

    return {
        "project": None,
        "agent": {"id": str(FAKE_AGENT_ID), "name": "Especialista em Produtos"},
        "projectPrompt": None,
        "agentPrompt": "Você é especialista em produtos.",
        "agentId": "11111111-1111-4111-8111-111111111111",
        "allowedActionIds": ["act.stock"],
        "capabilities": {"actions": True},
        "specialization": None,
    }


def _build_use_cases(*, common: bool):
    session = _session(agent_id=None if common else FAKE_AGENT_ID)
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

    llm_gateway = MagicMock()
    llm_gateway.generate.return_value = _LLM_ANSWER
    llm_gateway.stream.return_value = iter([_LLM_ANSWER])

    tool_context = {"context": "", "toolCalls": [], "nativeToolCalling": {}}
    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = tool_context

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {"context": "", "sources": []}

    prompt_policy_service = MagicMock()
    prompt_policy_service.build_contextual_prompt.return_value = "system"
    prompt_policy_service._load_policy.return_value = ""

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

    return session, SendChatMessageUseCase(**kwargs), StreamChatMessageUseCase(**kwargs), llm_gateway


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


def _assert_catalog_facts_in_llm(messages: list[dict], *, question: str, common: bool) -> None:
    user_messages = [item for item in messages if item.get("role") == "user"]
    assert user_messages
    content = user_messages[-1]["content"]
    assert question in content
    assert "Posso ajudar você nestes formatos:" in content
    assert "Robério" not in content
    if common:
        assert "chat comum" in content.lower()
    else:
        assert "Especialista em Produtos" in content


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


@pytest.fixture
def mock_action_catalog(monkeypatch):
    catalog = [
        {
            "actionId": "act.stock",
            "method": "GET",
            "path": "/api/v1/products/{code}/stock",
            "summary": "Estoque do produto",
        },
    ]

    monkeypatch.setattr(
        "app.application.services.chat_capabilities_service.ChatCapabilitiesService.load_action_catalog_for_agent",
        lambda allowed: catalog if allowed else [],
    )


@pytest.mark.parametrize("message", _CAPABILITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_capabilities_uses_llm_with_catalog_facts(
    message: str, common: bool, mock_action_catalog
):
    session, send_use_case, _, llm_gateway = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    response = send_use_case.execute(request)

    llm_gateway.generate.assert_called_once()
    _assert_catalog_facts_in_llm(
        llm_gateway.generate.call_args[0][0],
        question=message,
        common=common,
    )
    assert response.answer == _LLM_ANSWER


@pytest.mark.parametrize("message", _CAPABILITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_stream_capabilities_uses_llm_with_catalog_facts(
    message: str, common: bool, mock_action_catalog
):
    session, _, stream_use_case, llm_gateway = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    llm_gateway.stream.assert_called_once()
    _assert_catalog_facts_in_llm(
        llm_gateway.stream.call_args[0][0],
        question=message,
        common=common,
    )
    assert answer == _LLM_ANSWER


def test_stream_group_capability_inquiry_sends_catalog_facts_to_llm(
    mock_action_catalog, monkeypatch
):
    search_catalog = [
        {
            "actionId": "act.search",
            "method": "GET",
            "path": "/products/search",
            "summary": "Busca de produtos",
            "parametersSchema": [
                {"name": "description"},
                {"name": "group_code"},
            ],
        },
    ]

    monkeypatch.setattr(
        "app.application.services.chat_capabilities_service.ChatCapabilitiesService.load_action_catalog_for_agent",
        lambda allowed: search_catalog if allowed else [],
    )

    session, _, stream_use_case, llm_gateway = _build_use_cases(common=False)
    stream_use_case.turn_support.workspace_context_service.build_context.return_value = {
        **_workspace(common=False),
        "allowedActionIds": ["act.search"],
    }
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="vc coonsegue buscar um produto pelo seu grupo?",
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    if llm_gateway.stream.called:
        content = llm_gateway.stream.call_args[0][0][-1]["content"]
        assert "group_code" in content
        assert answer == _LLM_ANSWER
    else:
        assert "group_code" in answer
    assert events
    tool_event = next(event for event in events if event.get("type") == "tool_calls")
    assert tool_event.get("toolCalls") == []
