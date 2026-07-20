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


def test_build_does_not_crash_on_department_dashboard_multi_route():
    """Regressão: UnboundLocalError quando o compose não tem path /products/."""
    answer = ChatCompositeDirectAnswerService.build(
        "painel de indicadores da engenharia",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/dashboard/department-indicators",
                    "actionId": "dashboard-department-indicators",
                    "operationId": "get_dashboard_department_indicators",
                },
                data={"items": [], "summary": {}},
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/dashboard/department-idd",
                    "actionId": "dashboard-department-idd",
                    "operationId": "get_dashboard_department_idd",
                },
                data={"score": 7.5},
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/engineering/transforma/summary",
                    "actionId": "engineering-transforma-summary",
                    "operationId": "get_engineering_transforma_summary",
                },
                data={"items": []},
            ),
        ],
    )

    # Pode montar seções ou None conforme presenter; não pode lançar UnboundLocalError.
    assert answer is None or isinstance(answer, str)


def test_build_multi_product_codes_intro_skips_non_product_paths():
    intro = ChatCompositeDirectAnswerService._build_multi_product_codes_intro(
        "painel de indicadores da engenharia",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "path": "/dashboard/department-indicators",
                    "actionId": "dashboard-department-indicators",
                },
                data={},
            ),
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "path": "/dashboard/department-idd",
                    "actionId": "dashboard-department-idd",
                },
                data={},
            ),
        ],
    )

    assert intro is None
