import json

from app.application.services.chat_structure_comparison_orchestration_service import (
    ChatStructureComparisonOrchestrationService,
)
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent


class FakeSelectionService:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
    ):
        self.calls.append((product_code, intent))
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "product-structure", "parameters": {"code": product_code}},
            "reason": f"estrutura {product_code}",
        }


def _structure_message(product_code: str) -> dict:
    payload = {
        "root": {
            "code": product_code,
            "description": "PRODUTO",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50230002",
                "description": "PIECE",
                "type": "PI",
                "unit": "MI",
                "quantity": 1,
                "components": [],
            }
        ],
    }

    return {
        "role": "assistant",
        "content": "",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/structure",
                        "responsePreview": json.dumps(payload),
                    },
                }
            ]
        },
    }


def test_plan_structure_fetches_when_comparison_missing_second_product():
    service = FakeSelectionService()
    history = [
        {"role": "user", "content": "estrutura do 90260077"},
        _structure_message("90260077"),
    ]

    planned = ChatStructureComparisonOrchestrationService.plan_structure_fetches(
        service,
        message="compare as estruturas do 90260077 e 90260088",
        allowed_action_ids=["product-structure"],
        conversation_context="90260077 90260088",
        previous_messages=history,
        max_calls=3,
    )

    assert len(planned) == 1
    assert service.calls[0][0] == "90260088"
    assert service.calls[0][1] == ChatProductQueryIntent.STRUCTURE


def test_plan_structure_fetches_skips_when_two_complete_models_in_history():
    service = FakeSelectionService()
    history = [
        {"role": "user", "content": "estrutura do 90260077"},
        _structure_message("90260077"),
        {"role": "user", "content": "estrutura do 90260088"},
        _structure_message("90260088"),
    ]

    planned = ChatStructureComparisonOrchestrationService.plan_structure_fetches(
        service,
        message="compare as estruturas",
        allowed_action_ids=["product-structure"],
        previous_messages=history,
    )

    assert planned == []
    assert not service.calls
