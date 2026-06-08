from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_preparation_memory_context_service import (
    ChatTurnPreparationMemoryContextService,
)


def test_memory_context_builds_working_memory_and_conversation_context():
    session = MagicMock()
    session.id = uuid4()

    result = ChatTurnPreparationMemoryContextService.build(
        message="estoque do produto 90260123",
        workspace_context={"agentId": str(uuid4())},
        history_source=[
            {"role": "user", "content": "oi"},
            {"role": "assistant", "content": "Olá."},
        ],
        attachments=[],
        session=session,
        user_id=uuid4(),
        session_memory_service=None,
    )

    assert result.working_memory_snapshot is not None
    assert "workingMemory" in result.workspace_context
    assert isinstance(result.conversation_context, str)
