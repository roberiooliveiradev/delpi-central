"""Resposta direta de identidade do assistente (stream + send), sem LLM."""

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
    llm_gateway.generate.side_effect = AssertionError("LLM não deve ser chamado para identidade")
    llm_gateway.stream.side_effect = AssertionError("LLM stream não deve ser chamado para identidade")

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


@pytest.mark.parametrize("message", _IDENTITY_PHRASES)
@pytest.mark.parametrize("common", [True, False], ids=["chat_comum", "agente"])
def test_send_identity_direct_answer_without_llm(message: str, common: bool):
    session, send_use_case, _ = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    response = send_use_case.execute(request)

    assert "Posso ajudar você nestes formatos" not in response.answer
    assert "forneça seu nome e email" not in response.answer.lower()
    if message == "quem é vc?":
        assert "e-mail" in response.answer.lower() or "email" in response.answer.lower()
    if common and message == "quem é vc?":
        assert "Especialista em Produtos" not in response.answer
    if not common and message == "quem é vc?":
        assert "Especialista em Produtos" in response.answer


@pytest.mark.parametrize("message", ("quem é vc?",))
@pytest.mark.parametrize("common", [False], ids=["agente"])
def test_stream_identity_direct_answer_without_llm(message: str, common: bool):
    session, _, stream_use_case = _build_use_cases(common=common)
    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=message,
        access_token=None,
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    assert "Especialista em Produtos" in answer
    assert "nome ou e-mail" in answer.lower() or "e-mail" in answer.lower()
