from app.domain.services.chat_drawing_analysis_turn_service import (
    ChatDrawingAnalysisTurnService,
)


def test_resolve_skill_disabled_direct_answer():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="analise este desenho 90260140",
        attachment_ids=["a1"],
        agent_metadata={"skills": {}},
        skills={"drawingAnalysis": False},
    )

    assert turn is not None
    assert turn.direct_answer
    assert "drawing-analysis-delpi" in turn.direct_answer


def test_resolve_missing_pdf():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="validar cotas do desenho 90260140",
        attachment_ids=None,
        agent_metadata={
            "skills": {
                "drawing-analysis-delpi": {"engineering": True},
            }
        },
        skills={"drawingAnalysis": True},
    )

    assert turn is not None
    assert turn.direct_answer
    assert "PDF" in turn.direct_answer


def test_resolve_active_with_code():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="analise o desenho 90260140",
        attachment_ids=["a1"],
        agent_metadata={
            "skills": {
                "drawing-analysis-delpi": {"engineering": True},
            }
        },
        skills={"drawingAnalysis": True},
    )

    assert turn is not None
    assert turn.active
    assert turn.product_code == "90260140"
    assert turn.direct_answer is None
