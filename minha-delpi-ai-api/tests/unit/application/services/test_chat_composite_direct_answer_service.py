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


def test_build_analyser_with_empty_structure_sections_is_not_empty():
    payload = {
        "success": True,
        "data": {
            "product": {
                "code": "10080047",
                "description": "TERM. PINO RETO 20-14AWG",
                "type": "MP",
                "unit": "PC",
                "group_code": "1008",
                "active": "S",
                "default_warehouse": "01",
                "last_purchase_price": 0.047,
                "standard_cost": 0.04352,
                "last_revision_date": "20230927",
                "ncm_ipi_position": "85369090",
                "barcode": "10080047",
            },
            "structure": {
                "root": None,
                "items": [],
                "total": 0,
                "total_pages": 0,
            },
            "guide": {"items": [], "total": 0},
            "inspection": {"items": [], "total": 0},
        },
    }

    answer = ChatCompositeDirectAnswerService.build(
        "ficha completa do produto 10080047",
        [
            ExternalActionExecutionResult(
                metadata={
                    "ok": True,
                    "statusCode": 200,
                    "path": "/products/10080047/analyser",
                    "actionId": "api_delpi.products.get_product_analyser",
                },
                data=payload,
            ),
        ],
    )

    assert answer is not None
    assert "10080047" in answer
    assert "TERM. PINO RETO" in answer
    assert "Atenção" not in answer
    assert "não retornou registros" not in answer.lower()
