from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.chat_session_memory_pins_use_case import ChatSessionMemoryPinsUseCase
from app.domain.exceptions.chat_exceptions import ChatSessionAccessDeniedError


def test_add_pin_persists_entity():
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

    memory_repo.upsert_entity.assert_called_once_with(session_id, "warehouse", "01")
    assert len(result["chips"]) == 2


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
