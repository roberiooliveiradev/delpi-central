"""Persistência incremental no stream: pergunta cedo, placeholder assistant, resposta no fim."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
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


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_stream_turn_execution_service.Settings.CHAT_PERSIST_BEFORE_PLAYBACK",
        True,
    )
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_stream_turn_execution_service.Settings.CHAT_FAST_PATH_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
    )


from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime


@pytest.fixture(autouse=True)
def patch_intelligence_runtime(monkeypatch):
    patch_resolve_chat_intelligence_runtime(monkeypatch)


def test_stream_emits_user_persisted_before_prepare_activity(monkeypatch):
    session = _session()
    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_all_messages_by_session.return_value = []
    chat_repository.create_message.side_effect = [user_message, assistant_message]
    chat_repository.update_assistant_message.return_value = assistant_message

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
    }

    llm_gateway = MagicMock()
    llm_gateway.stream.return_value = iter(["Resposta ", "final."])

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {"context": "", "sources": []}

    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = {
        "context": "",
        "toolCalls": [],
        "directAnswer": None,
        "skipRag": False,
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
    )

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="pesquise na internet sobre Python",
        access_token=None,
    )

    events = list(use_case.stream(request))
    event_types = [event.get("type") for event in events]

    assert event_types.index("user_persisted") < event_types.index("activity")
    assert "assistant_pending" in event_types
    assert event_types.index("assistant_pending") < event_types.index("done")

    user_create_call = chat_repository.create_message.call_args_list[0]
    assert user_create_call.kwargs["role"] == "user"
    assert user_create_call.kwargs["content"] == request.message

    chat_repository.patch_message_metadata.assert_called_once()

    # A pergunta deve virar a folha ativa imediatamente (antes do assistente),
    # para aparecer ao reabrir a conversa mesmo se o usuário sair antes do fim.
    leaf_calls = chat_repository.set_active_leaf_message_id.call_args_list
    assert leaf_calls, "deve apontar o ramo ativo para a pergunta imediatamente"
    assert leaf_calls[0].kwargs["message_id"] == user_message.id


def test_resend_emits_user_persisted_before_prepare(monkeypatch):
    session = _session()
    anchor_id = uuid4()
    anchor = ChatMessage(
        id=anchor_id,
        session_id=session.id,
        role="user",
        content="ola",
        metadata=None,
        created_at=datetime.now(timezone.utc),
        parent_message_id=None,
    )
    branch_user = MagicMock()
    branch_user.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()

    chat_repository = MagicMock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.get_user_message_for_user.return_value = anchor
    chat_repository.list_all_messages_by_session.return_value = [anchor]
    chat_repository.create_message.side_effect = [branch_user, assistant_message]
    chat_repository.update_assistant_message.return_value = assistant_message

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
    }

    llm_gateway = MagicMock()
    llm_gateway.stream.return_value = iter(["Resposta ", "editada."])

    rag_context_service = MagicMock()
    rag_context_service.build_context.return_value = {"context": "", "sources": []}

    chat_tool_context_service = MagicMock()
    chat_tool_context_service.build_context.return_value = {
        "context": "",
        "toolCalls": [],
        "directAnswer": None,
        "skipRag": False,
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
    )

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="ola editado",
        access_token=None,
        resend_from_message_id=str(anchor_id),
    )

    events = list(use_case.stream(request))
    event_types = [event.get("type") for event in events]

    assert event_types.index("user_persisted") < event_types.index("activity")
    assert chat_repository.create_message.call_args_list[0].kwargs["role"] == "user"
    assert chat_repository.create_message.call_args_list[0].kwargs["content"] == "ola editado"
    chat_repository.set_active_leaf_message_id.assert_called()
