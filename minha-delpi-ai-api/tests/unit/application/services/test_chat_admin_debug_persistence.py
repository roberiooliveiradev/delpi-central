"""adminDebug: sempre persiste; exposição ao cliente só com admin_debug=True."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.use_cases.send_chat_message_use_case import SendChatMessageUseCase
from app.application.use_cases.stream_chat_message_use_case import StreamChatMessageUseCase
from app.domain.entities.chat_session import ChatSession


@pytest.fixture(autouse=True)
def patch_intelligence_runtime(monkeypatch):
    from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime

    patch_resolve_chat_intelligence_runtime(monkeypatch)


@pytest.fixture(autouse=True)
def patch_chat_settings(monkeypatch):
    for module in (
        "app.application.use_cases.send_chat_message_use_case",
        "app.application.use_cases.stream_chat_message_use_case",
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
        "app.application.services.chat_turn.chat_turn_completion_service.ChatTurnCompletionService._estimate_cost",
        lambda self, **kwargs: None,
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


def _build_use_cases():
    session = _session()
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
        "agent": None,
        "projectPrompt": None,
        "agentPrompt": None,
        "agentId": None,
        "allowedActionIds": [],
        "capabilities": {},
        "specialization": None,
        "skills": {},
    }

    llm_gateway = MagicMock()
    llm_gateway.generate.return_value = "Olá!"
    llm_gateway.stream.return_value = iter(["Olá", "!"])

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

    return kwargs, chat_repository, session


def _assistant_metadata(chat_repository) -> dict:
    assistant_call = chat_repository.create_message.call_args_list[-1]
    return assistant_call.kwargs.get("metadata") or assistant_call[1].get("metadata")


def test_send_always_persists_admin_debug_even_without_expose_flag():
    kwargs, chat_repository, session = _build_use_cases()
    use_case = SendChatMessageUseCase(**kwargs)

    response = use_case.execute(
        SendChatMessageRequest(
            user_id=str(session.user_id),
            session_id=str(session.id),
            message="ola",
            admin_debug=False,
        )
    )

    metadata = _assistant_metadata(chat_repository)

    assert "adminDebug" in metadata
    assert metadata["adminDebug"].get("recordedAt")
    assert response.adminDebug is None


def test_send_exposes_admin_debug_when_flag_true():
    kwargs, chat_repository, session = _build_use_cases()
    use_case = SendChatMessageUseCase(**kwargs)

    response = use_case.execute(
        SendChatMessageRequest(
            user_id=str(session.user_id),
            session_id=str(session.id),
            message="ola",
            admin_debug=True,
        )
    )

    metadata = _assistant_metadata(chat_repository)

    assert response.adminDebug is not None
    assert response.adminDebug == metadata["adminDebug"]


def test_stream_persists_always_exposes_only_with_flag():
    kwargs, chat_repository, session = _build_use_cases()
    use_case = StreamChatMessageUseCase(**kwargs)

    events_hidden = list(
        use_case.stream(
            SendChatMessageRequest(
                user_id=str(session.user_id),
                session_id=str(session.id),
                message="ola",
                admin_debug=False,
            )
        )
    )
    done_hidden = next(e for e in events_hidden if e.get("type") == "done")
    metadata_hidden = _assistant_metadata(chat_repository)

    assert "adminDebug" in metadata_hidden
    assert done_hidden.get("adminDebug") is None

    chat_repository.reset_mock()
    chat_repository.get_session_by_id.return_value = session
    chat_repository.list_messages_by_session.return_value = []
    user_message = MagicMock()
    user_message.id = uuid4()
    assistant_message = MagicMock()
    assistant_message.id = uuid4()
    chat_repository.create_message.side_effect = [user_message, assistant_message]

    events_visible = list(
        use_case.stream(
            SendChatMessageRequest(
                user_id=str(session.user_id),
                session_id=str(session.id),
                message="ola",
                admin_debug=True,
            )
        )
    )
    done_visible = next(e for e in events_visible if e.get("type") == "done")
    metadata_visible = _assistant_metadata(chat_repository)

    assert done_visible.get("adminDebug") == metadata_visible["adminDebug"]
