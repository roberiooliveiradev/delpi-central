"""Regressão multi-turno: estoque → filtre filial (stream + send sem LLM/RAG)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession

_STOCK_HISTORY = [
    {"role": "user", "content": "estoque do produto 10080022"},
    {
        "role": "assistant",
        "content": "Estoque do produto 10080022",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080022/stock",
                        "actionId": "stock-action",
                    },
                }
            ]
        },
    },
]

_REFINEMENT_MESSAGE = "filtre filial 02"
_DIRECT_ANSWER = (
    "**Estoque do produto 10080022 (filial 02):**\n\n"
    "- **Filial:** 02\n- **Disponível:** 120 un"
)


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


def _workspace() -> dict:
    return {
        "project": None,
        "agent": None,
        "projectPrompt": None,
        "agentPrompt": None,
        "agentId": None,
        "allowedActionIds": ["stock-action"],
        "capabilities": {"actions": True},
        "specialization": None,
        "skills": {"companyKnowledge": True},
    }


def _tool_context_with_direct_answer() -> dict:
    return {
        "context": "consulta estoque filial 02",
        "toolCalls": [
            {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": "stock-action",
                    "parameters": {"code": "10080022", "branch": "02"},
                },
                "metadata": {
                    "ok": True,
                    "path": "/products/10080022/stock",
                    "actionId": "stock-action",
                },
            }
        ],
        "directAnswer": _DIRECT_ANSWER,
        "nativeToolCalling": {},
    }


def _build_use_cases():
    session = _session()
    workspace = _workspace()
    captured_assistant_metadata: dict = {}

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_messages_by_session.return_value = _STOCK_HISTORY
    user_message = MagicMock()
    user_message.id = uuid4()
    chat_repository.create_message.return_value = user_message
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
    def _create_message(session_id, role, content, metadata=None, **kwargs):
        if role == "assistant":
            captured_assistant_metadata.update(metadata or {})
            return assistant_message
        if role == "user":
            return user_message
        return MagicMock(id=uuid4())

    chat_repository.create_message.side_effect = _create_message

    def _update_assistant(_message_id, _answer, metadata):
        captured_assistant_metadata.update(metadata or {})
        return assistant_message

    chat_repository.update_assistant_message.side_effect = _update_assistant

    workspace_context_service = MagicMock()
    workspace_context_service.build_context.return_value = workspace

    llm_gateway = MagicMock()
    llm_gateway.generate.side_effect = AssertionError("LLM não deve ser chamado no refino de estoque")
    llm_gateway.stream.side_effect = AssertionError("LLM stream não deve ser chamado no refino de estoque")

    tool_context = _tool_context_with_direct_answer()
    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = tool_context

    rag_context_service = MagicMock()
    rag_context_service.build_context.side_effect = AssertionError(
        "RAG não deve ser consultado no refino operacional"
    )

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
        chat_tool_context_service,
        captured_assistant_metadata,
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
        monkeypatch.setattr(f"{module}.Settings.CHAT_FAST_PATH_ENABLED", True)
        monkeypatch.setattr(
            f"{module}.Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED",
            True,
        )
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


def test_send_stock_branch_refinement_uses_direct_answer_without_llm_or_rag():
    session, send_use_case, _, rag_context_service, llm_gateway, tool_context_service, _ = (
        _build_use_cases()
    )

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=_REFINEMENT_MESSAGE,
        access_token="token",
    )

    response = send_use_case.execute(request)

    assert "filial 02" in response.answer.lower() or "02" in response.answer
    llm_gateway.generate.assert_not_called()
    rag_context_service.build_context.assert_not_called()
    tool_context_service.build_context.assert_called_once()


def test_stream_stock_branch_refinement_streams_direct_answer_without_llm_or_rag():
    (
        session,
        _,
        stream_use_case,
        rag_context_service,
        llm_gateway,
        tool_context_service,
        captured_assistant_metadata,
    ) = _build_use_cases()

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message=_REFINEMENT_MESSAGE,
        access_token="token",
    )

    events = list(stream_use_case.stream(request))
    answer = _collect_stream_answer(events)

    assert _DIRECT_ANSWER.strip() in answer or "filial" in answer.lower()
    llm_gateway.stream.assert_not_called()
    rag_context_service.build_context.assert_not_called()
    tool_context_service.build_context.assert_called_once()

    pipeline = (
        captured_assistant_metadata.get("intelligence", {}).get("pipeline", {})
    )
    assert pipeline.get("skipRag") is True
    assert "skip_rag" in (pipeline.get("stages") or [])
