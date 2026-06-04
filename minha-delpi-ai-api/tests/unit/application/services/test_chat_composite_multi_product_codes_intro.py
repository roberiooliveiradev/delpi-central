from app.application.services.chat_composite_direct_answer_service import (
    ChatCompositeDirectAnswerService,
    ExternalActionExecutionResult,
)


def test_build_multi_product_codes_intro_for_parents_batch():
    answer = ChatCompositeDirectAnswerService.build(
        "onde são usados os produtos 10080022, 10080012?",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/10080022/parents",
                    "actionId": "product-parents",
                },
                data={
                    "items": [
                        {
                            "code": "PA-01",
                            "description": "Produto pai",
                            "type": "PA",
                            "quantity": 1,
                        }
                    ],
                    "total": 1,
                },
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/10080012/parents",
                    "actionId": "product-parents",
                },
                data={
                    "items": [
                        {
                            "code": "PA-02",
                            "description": "Outro pai",
                            "type": "PA",
                            "quantity": 1,
                        }
                    ],
                    "total": 1,
                },
            ),
        ],
    )

    assert answer is not None
    assert "10080022" in answer
    assert "10080012" in answer
    assert "onde o item é usado" in answer.lower() or "usado" in answer.lower()
    assert "###" in answer


def test_build_multi_product_codes_intro_for_stock_batch():
    answer = ChatCompositeDirectAnswerService.build(
        "estoque dos produtos 10080022, 10080012?",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/10080022/stock",
                    "actionId": "product-stock",
                },
                data={"items": [], "total": 0},
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/10080012/stock",
                    "actionId": "product-stock",
                },
                data={"items": [], "total": 0},
            ),
        ],
    )

    assert answer is not None
    assert "10080022" in answer
    assert "10080012" in answer
    assert "estoque" in answer.lower()
