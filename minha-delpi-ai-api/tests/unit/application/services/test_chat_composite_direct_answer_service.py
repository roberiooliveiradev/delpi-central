from app.application.services.chat_composite_direct_answer_service import (
    ChatCompositeDirectAnswerService,
    ExternalActionExecutionResult,
)


def test_build_composite_with_success_and_failure():
    answer = ChatCompositeDirectAnswerService.build(
        "estrutura do 90260077 e 90260088",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/90260077/structure",
                    "actionId": "product-structure",
                },
                data={
                    "root": {
                        "code": "90260077",
                        "description": "CHICOTE",
                        "type": "PA",
                        "unit": "MI",
                        "quantity": 1,
                    },
                    "items": [
                        {
                            "code": "50230002",
                            "description": "CB14AMAR",
                            "type": "PI",
                            "unit": "MI",
                            "quantity": 1,
                            "components": [],
                        }
                    ],
                },
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": False,
                    "statusCode": 404,
                    "path": "/products/90260088/structure",
                    "actionId": "product-structure",
                },
                data=None,
            ),
        ],
    )

    assert answer is not None
    assert "90260077" in answer
    assert "Atenção" in answer
    assert "404" in answer or "não encontrado" in answer.lower()
