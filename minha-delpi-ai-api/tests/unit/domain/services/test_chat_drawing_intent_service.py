from app.domain.services.chat_drawing_intent_service import (
    DRAWING_ANALYSIS_SKILL_KEY,
    ChatDrawingIntentService,
)


def test_is_drawing_analysis_explicit_trigger():
    assert ChatDrawingIntentService.is_drawing_analysis_request(
        "Analise este desenho 90260140"
    )


def test_is_drawing_analysis_with_pdf_vocabulary():
    assert ChatDrawingIntentService.is_drawing_analysis_request(
        "conferir decapes do pdf anexado",
        attachment_ids=["att-1"],
    )


def test_wants_product_analyser_with_code():
    assert ChatDrawingIntentService.wants_product_analyser(
        "validar desenho do produto 90260140"
    )


def test_requires_pdf_when_no_attachment():
    assert ChatDrawingIntentService.requires_pdf_for_full_analysis(
        "validar cotas do desenho",
        attachment_ids=None,
    )


def test_normalize_skill_alias():
    assert (
        ChatDrawingIntentService.normalize_skill_key("drawing-analyser")
        == DRAWING_ANALYSIS_SKILL_KEY
    )


def test_missing_pdf_answer():
    assert "anexe o pdf" in ChatDrawingIntentService.build_missing_pdf_answer().lower()
