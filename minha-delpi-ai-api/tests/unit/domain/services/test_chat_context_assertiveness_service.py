from app.domain.services.chat_context_assertiveness_service import (
    ChatContextAssertivenessService,
)


def test_evaluate_turn_flags_supplier_question_with_analyser():
    result = ChatContextAssertivenessService.evaluate_turn(
        message="Quem fornece o produto 10080001?",
        answer="Produto **None**: None.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"path": "/products/10080001/analyser", "ok": True},
            }
        ],
        snapshot={"followUpDetected": False, "lastEntities": {}},
    )

    assert result["score"] < 70
    assert "supplier_intent_used_analyser" in result["flags"]
    assert "humanized_none_fields" in result["flags"]


def test_evaluate_turn_rewards_follow_up_entity_reuse():
    result = ChatContextAssertivenessService.evaluate_turn(
        message="agora estoque",
        answer="Estoque do produto 10080001.",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"path": "/products/10080001/stock", "ok": True},
            }
        ],
        snapshot={
            "followUpDetected": True,
            "lastEntities": {"productCode": "10080001"},
            "resolvedReferences": [
                {
                    "text": "follow-up operacional",
                    "resolvedTo": "productCode",
                    "value": "10080001",
                    "confidence": 0.9,
                }
            ],
        },
    )

    assert result["followUpResolved"] is True
    assert result["score"] >= 80
