from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.chat_session_memory_pins_use_case import ChatSessionMemoryPinsUseCase
from app.domain.exceptions.chat_exceptions import ChatSessionAccessDeniedError


def test_add_pin_persists_as_context_item():
    session_id = uuid4()
    user_id = uuid4()
    session = MagicMock()
    session.user_id = user_id

    session_repo = MagicMock()
    session_repo.get_session_by_id.return_value = session

    memory_repo = MagicMock()
    memory_repo.load_active_overlay.return_value = {
        "lastEntities": {"branch": "02", "warehouse": "01"},
        "behaviorInstructions": {},
    }

    use_case = ChatSessionMemoryPinsUseCase(session_repo, memory_repo)
    result = use_case.add_pin(
        user_id=user_id,
        session_id=session_id,
        kind="warehouse",
        value="01",
    )

    memory_repo.add_context_item.assert_called_once()
    saved_item = memory_repo.add_context_item.call_args[0][1]
    assert saved_item.get("kind") == "context"
    assert saved_item.get("extractedEntities", {}).get("warehouse") == "01"


def test_add_pin_rejects_invalid_value():
    session_id = uuid4()
    user_id = uuid4()
    session = MagicMock()
    session.user_id = user_id

    session_repo = MagicMock()
    session_repo.get_session_by_id.return_value = session
    memory_repo = MagicMock()

    use_case = ChatSessionMemoryPinsUseCase(session_repo, memory_repo)

    with pytest.raises(ValueError):
        use_case.add_pin(
            user_id=user_id,
            session_id=session_id,
            kind="product",
            value="x",
        )


def test_add_context_item_replaces_duplicate_message_reference():
    session_id = uuid4()
    user_id = uuid4()
    session = MagicMock()
    session.user_id = user_id

    session_repo = MagicMock()
    session_repo.get_session_by_id.return_value = session

    old_item = {
        "id": "old-item",
        "kind": "question",
        "label": "Pergunta: SA1",
        "content": "texto antigo",
        "messageId": "msg-1",
    }

    memory_repo = MagicMock()
    memory_repo.load_active_overlay.return_value = {
        "lastEntities": {},
        "behaviorInstructions": {},
        "userContextItems": [old_item],
    }

    use_case = ChatSessionMemoryPinsUseCase(session_repo, memory_repo)
    use_case.add_context_item(
        user_id=user_id,
        session_id=session_id,
        content="texto novo",
        role="user",
        message_id="msg-1",
    )

    memory_repo.remove_context_item.assert_called_once_with(session_id, "old-item")
    assert memory_repo.add_context_item.call_count == 1


def test_add_context_item_ingests_question_answer_turn():
    session_id = uuid4()
    user_id = uuid4()
    session = MagicMock()
    session.user_id = user_id

    session_repo = MagicMock()
    session_repo.get_session_by_id.return_value = session

    memory_repo = MagicMock()
    memory_repo.load_active_overlay.return_value = {
        "lastEntities": {},
        "behaviorInstructions": {},
        "userContextItems": [],
    }

    use_case = ChatSessionMemoryPinsUseCase(session_repo, memory_repo)
    use_case.add_context_item(
        user_id=user_id,
        session_id=session_id,
        content="",
        question="Qual o estoque do 10080001?",
        answer="12 unidades na filial 02.",
        question_message_id="q-msg",
        answer_message_id="a-msg",
    )

    assert memory_repo.add_context_item.call_count == 2
    kinds = [
        call.args[1].get("kind")
        for call in memory_repo.add_context_item.call_args_list
    ]
    assert "question" in kinds
    assert "answer" in kinds


def test_remove_pin_checks_access():
    session_id = uuid4()
    user_id = uuid4()
    other_user = uuid4()
    session = MagicMock()
    session.user_id = other_user

    session_repo = MagicMock()
    session_repo.get_session_by_id.return_value = session
    memory_repo = MagicMock()

    use_case = ChatSessionMemoryPinsUseCase(session_repo, memory_repo)

    with pytest.raises(ChatSessionAccessDeniedError):
        use_case.remove_pin(user_id=user_id, session_id=session_id, kind="branch")
