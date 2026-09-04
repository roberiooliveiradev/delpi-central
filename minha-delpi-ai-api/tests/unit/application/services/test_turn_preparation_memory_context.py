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


def _build_with_prior_turn_facts(response_mode: str | None):
    session = MagicMock()
    session.id = uuid4()
    history = [
        {"role": "user", "content": "liste terminais pino"},
        {
            "role": "assistant",
            "content": "Segue a lista.",
            "metadata": {
                "contextSnapshot": {
                    "lastResultExcerpt": {
                        "identityFields": {
                            "code": "10080001",
                            "description": "TERMINAL PINO 6MM LATAO",
                        }
                    },
                    "resultSets": [
                        {
                            "id": "rs-1",
                            "kind": "product",
                            "totalCount": 20,
                            "items": [
                                {
                                    "ordinal": index,
                                    "code": f"1008000{index}",
                                    "label": f"TERMINAL PINO {index} MM LATAO ESTANHADO",
                                }
                                for index in range(1, 10)
                            ],
                        }
                    ],
                }
            },
        },
    ]

    return ChatTurnPreparationMemoryContextService.build(
        message="e o estoque do segundo?",
        workspace_context={"agentId": str(uuid4())},
        history_source=history,
        attachments=[],
        session=session,
        user_id=uuid4(),
        session_memory_service=None,
        response_mode=response_mode,
    )


def test_memory_context_records_response_mode_in_snapshot():
    result = _build_with_prior_turn_facts("fast")

    assert result.working_memory_snapshot.get("responseMode") == "fast"


def test_memory_context_defaults_response_mode_to_normal():
    result = _build_with_prior_turn_facts(None)

    assert result.working_memory_snapshot.get("responseMode") == "normal"


def test_memory_context_normalizes_response_mode_alias():
    result = _build_with_prior_turn_facts("pensador")

    assert result.working_memory_snapshot.get("responseMode") == "thinker"
