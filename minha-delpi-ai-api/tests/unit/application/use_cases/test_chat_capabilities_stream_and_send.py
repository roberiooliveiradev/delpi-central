"""Garante resposta direta de capacidades no chat comum e com agente (stream + send)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession

_CAPABILITY_PHRASES = (
    "o que vc faz?",
    "o que vc é capaz de fazer?",
    "ajuda",
    "o que você pode fazer?",
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
        }

    return {
        "project": None,
        "agent": {"key": "produtos", "name": "Especialista em Produtos"},
        "projectPrompt": None,
        "agentPrompt": "Você é especialista em produtos.",
        "agentKey": "produtos",
        "allowedActionIds": ["act.stock"],
        "capabilities": {"actions": True},
        "specialization": None,
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

    llm_gateway = MagicMock()
    llm_gateway.generate.side_effect = AssertionError("LLM não deve ser chamado para capacidades")
    llm_gateway.stream.side_effect = AssertionError("LLM stream não deve ser chamado para capacidades")

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

    return session, SendChatMessageUseCase(**kwargs), StreamChatMessageUseCase(**kwargs)


def _collect_stream_answer(events: list[dict]) -> str:
    return "".join(
        event.get("content", "")
        for event in events
        if event.get("type") == "token"
    )


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
        "app.application.use_cases.send_chat_message_use_case.ChatCapabilitiesService.load_action_catalog_for_agent",
        lambda allowed: catalog if allowed else [],
    )
    monkeypatch.setattr(
        "app.application.use_cases.stream_chat_message_use_case.ChatCapabilitiesService.load_action_catalog_for_agent",
        lambda allowed: catalog if allowed else [],
    )


@pytest.mark.parametrize("message", _CAPABILITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_capabilities_direct_answer_without_llm(
    message: str, common: bool, mock_action_catalog
):
    session, send_use_case, _ = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    response = send_use_case.execute(request)

    assert response.answer.startswith("Posso ajudar você nestes formatos:")
    assert "Gerenciamento de Permissões" not in response.answer
    if common:
        assert "chat comum" in response.answer.lower()
        assert "Especialista em Produtos" not in response.answer
    else:
        assert "Especialista em Produtos" in response.answer
        assert "estoque do produto 10080001" in response.answer


@pytest.mark.parametrize("message", _CAPABILITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_stream_capabilities_direct_answer_without_llm(
    message: str, common: bool, mock_action_catalog
):
    session, _, stream_use_case = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    assert answer.startswith("Posso ajudar você nestes formatos:")
    assert "Como seu assistente corporativo" not in answer
    if common:
        assert "chat comum" in answer.lower()
    else:
        assert "Especialista em Produtos" in answer
        assert "Consultas operacionais" in answer
