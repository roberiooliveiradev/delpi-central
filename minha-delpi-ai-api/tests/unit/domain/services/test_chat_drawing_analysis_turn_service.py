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


def test_resolve_missing_product_code_without_attachment():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="validar cotas do desenho",
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
    assert "90260140" in turn.direct_answer or "código" in turn.direct_answer.lower()


def test_resolve_does_not_inherit_code_from_history_without_attachment():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="analise o desenho",
        attachment_ids=None,
        previous_messages=[
            {"role": "user", "content": "analise o desenho 90262957"},
            {"role": "assistant", "content": "Relatório gerado."},
        ],
        agent_metadata={
            "skills": {
                "drawing-analysis-delpi": {"engineering": True},
            }
        },
        skills={"drawingAnalysis": True},
    )

    assert turn is not None
    assert turn.direct_answer
    assert turn.product_code is None


def test_resolve_multiple_codes_without_attachment():
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="analise o desenho 90262957 e 90263489",
        attachment_ids=None,
        agent_metadata={
            "skills": {
                "drawing-analysis-delpi": {"engineering": True},
            }
        },
        skills={"drawingAnalysis": True},
    )

    assert turn is not None
    assert turn.direct_answer is None
    assert turn.product_codes == ("90262957", "90263489")
    assert turn.product_code == "90262957"


def test_resolve_continues_with_product_code_without_attachment():
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
    assert turn.active
    assert turn.product_code == "90260140"
    assert turn.direct_answer is None
    assert turn.requires_pdf is True


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
