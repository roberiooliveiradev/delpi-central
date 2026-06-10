from app.application.services.chat_data_interpretation_answer_service import (
    ChatDataInterpretationAnswerService,
)


def test_build_answer_from_humanized_summary():
    history = [
        {
            "role": "assistant",
            "content": "Visualização dos dados",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260142/guide",
                            "humanizedSummary": {
                                "titulo": "Roteiro do produto 90260142",
                                "linhas": [
                                    "O produto **90260142** possui 2 operação(ões): **10** Montagem.",
                                    "- Operação **10**: Montagem no centro **C01**.",
                                ],
                            },
                        },
                    }
                ]
            },
        }
    ]

    answer = ChatDataInterpretationAnswerService.build_answer(
        "explique os dados acima",
        history,
    )

    assert answer
    assert "90260142" in answer
    assert "Montagem" in answer
    assert "superadmin" not in answer.lower()


def test_build_resume_from_stock_preview():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                            "humanizedSummary": {
                                "titulo": "Consulta SQL",
                                "linhas": ["A consulta retornou **5** registro(s)."],
                            },
                            "responsePreview": (
                                '{"items": [{"branch": "01", "warehouse": "01", '
                                '"current_quantity": 100, "available_quantity": 80, '
                                '"committed_quantity": 5, "physical_location": "A1"}]}'
                            ),
                        },
                    }
                ]
            },
        }
    ]

    answer = ChatDataInterpretationAnswerService.build_answer("resume", history)

    assert answer
    assert "10080022" in answer
    assert "01" in answer
    assert "80" in answer


def test_returns_none_without_tool_history():
    assert ChatDataInterpretationAnswerService.build_answer("resume", []) is None


def test_build_answer_prefers_data_commentary_over_generic_summary():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90262404/factory-status",
                            "humanizedSummary": {
                                "titulo": "Status fabril — 90262404",
                                "linhas": ["Situação consolidada: **PA PRODUZIDO**"],
                            },
                            "dataCommentary": {
                                "profileKey": "factory_status",
                                "highlights": [
                                    "Produção **em andamento** — PA **Sim** · PI **Não**.",
                                    "MP **10160001** com cobertura baixa.",
                                ],
                                "attention": ["Validar compra ou substituição."],
                                "narrativeInsight": "Produção ativa com atenção em MP 10160001.",
                            },
                        },
                    }
                ]
            },
        }
    ]

    answer = ChatDataInterpretationAnswerService.build_answer(
        "explique isso",
        history,
    )

    assert answer
    assert "10160001" in answer
    assert "Produção" in answer
    assert "Atenção" in answer or "Validar compra" in answer
