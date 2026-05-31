from app.application.services.chat_drawing_follow_up_turn_service import (
    ChatDrawingFollowUpTurnService,
)


def _assistant_with_drawing() -> list[dict]:
    return [
        {
            "role": "assistant",
            "metadata": {
                "drawingAnalysis": {
                    "productCode": "90260140",
                    "items": [
                        {
                            "section": "BOM",
                            "item": "Componente X",
                            "status": "critical_error",
                            "pdfEvidence": "PDF",
                            "apiEvidence": "API",
                            "recommendation": "Corrigir",
                        },
                        {
                            "section": "Cotas",
                            "item": "Comprimento",
                            "status": "ok",
                            "recommendation": "—",
                        },
                    ],
                }
            },
        }
    ]


def test_critical_only_follow_up_from_history():
    answer = ChatDrawingFollowUpTurnService.resolve_direct_answer(
        "mostre apenas os erros críticos do relatório de análise do desenho 90260140",
        previous_messages=_assistant_with_drawing(),
    )

    assert answer
    assert "Erros críticos" in answer
    assert "Componente X" in answer
    assert "Comprimento" not in answer


def test_reanalysis_not_intercepted():
    answer = ChatDrawingFollowUpTurnService.resolve_direct_answer(
        "reanalise o desenho técnico 90260140 com o PDF anexado",
        previous_messages=_assistant_with_drawing(),
    )

    assert answer is None
