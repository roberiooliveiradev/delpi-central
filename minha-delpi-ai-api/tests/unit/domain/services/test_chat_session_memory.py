"""Regressão — memória de sessão e preferências (Playbook 01)."""

from uuid import uuid4

import pytest

from app.application.services.chat_session_memory_service import ChatSessionMemoryService
from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from tests.fixtures.chat_intelligence_regression_cases import (
    SESSION_MEMORY_BEHAVIOR_CASES,
    SESSION_MEMORY_CLEAR_CASES,
    SESSION_MEMORY_REFERENCE_CASES,
)


def _assistant_with_stock(product_code: str = "10080001"):
    return {
        "role": "assistant",
        "content": f"Estoque do produto {product_code}",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/stock",
                        "presentation": {"type": "table", "title": "Estoque"},
                    },
                }
            ],
        },
    }


@pytest.mark.parametrize("message,entities,expected_keys", SESSION_MEMORY_REFERENCE_CASES)
def test_reference_resolution_from_snapshot(message, entities, expected_keys):
    snapshot = {
        "operationalFocus": entities,
        "lastPresentation": {"type": "table", "messageId": "msg-1"},
        "lastAction": {"name": "stock_lookup", "params": entities},
    }
    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(message, snapshot)

    for key in expected_keys:
        assert key in used


@pytest.mark.parametrize("message,should_clear", SESSION_MEMORY_CLEAR_CASES)
def test_clear_context_detection(message, should_clear):
    assert ChatSessionMemoryService.is_clear_context_request(message) is should_clear


@pytest.mark.parametrize("message,expected", SESSION_MEMORY_BEHAVIOR_CASES)
def test_behavior_preferences_detected(message, expected):
    detected = ChatBehaviorInstructionService.detect(message)

    for key, value in expected.items():
        assert detected.get(key) == value


def test_m1_stock_then_suppliers_inherits_product():
    previous = [_assistant_with_stock("10080001")]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="e os fornecedores?",
        previous_messages=previous,
    )

    assert snapshot["operationalFocus"].get("productCode") == "10080001"
    assert snapshot["followUpDetected"] is True


def test_m3_short_answer_preference_in_prompt():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="daqui pra frente responda curto",
        previous_messages=[],
    )
    block = ChatConversationMemoryService.format_prompt_block(snapshot)

    assert snapshot["behaviorInstructions"].get("answerLength") == "short"
    assert "curtas" in block.lower()


def test_m6_clear_context_wipes_entities():
    class _Repo:
        def deactivate_all(self, session_id):
            return 1

    service = ChatSessionMemoryService(_Repo())
    snapshot = service.apply_to_pre_turn(
        session_id=uuid4(),
        snapshot={"operationalFocus": {"productCode": "10080001"}},
        message="limpe o contexto",
    )

    assert snapshot["operationalFocus"] == {}
    assert snapshot.get("persistedMemoryCleared") is True


def test_m7_agent_switch_clears_last_action():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="estoque",
        previous_messages=[_assistant_with_stock()],
        previous_agent_id="agent-a",
        agent_id="agent-b",
    )

    assert snapshot.get("agentContextReset") is True
    assert "lastAction" not in snapshot or snapshot.get("lastAction") is None


def test_m10_post_turn_enriches_last_action():
    snapshot = ChatConversationMemoryService.build_post_turn(
        message="estoque do produto 10080001",
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080001/stock",
                    "presentation": {"type": "table"},
                },
            }
        ],
    )

    assert snapshot.get("lastAction", {}).get("name") == "stock_lookup"


def test_m11_selective_clear_product():
    snapshot = {
        "operationalFocus": {"productCode": "10080001", "branch": "02"},
        "behaviorInstructions": {},
    }
    snapshot = ChatConversationMemoryService._apply_selective_clear(
        "esqueça esse produto",
        snapshot,
    )

    assert "productCode" not in snapshot["operationalFocus"]
    assert snapshot["operationalFocus"].get("branch") == "02"


def test_m5_canvas_state_in_snapshot():
    previous = [
        {
            "role": "assistant",
            "metadata": {
                "canvasOpen": {
                    "title": "Relatório",
                    "markdown": "# Título",
                }
            },
        }
    ]
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="corrija o texto da lousa",
        previous_messages=previous,
    )

    assert snapshot.get("canvas", {}).get("active") is True
