from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService


def test_drawing_query_intent_bundle_has_vocabulary():
    assert ChatAssistantContentService.list("drawing_query_intent", "explicitTriggers")
    assert ChatAssistantContentService.list("drawing_query_intent", "attachmentVocabulary")
    assert ChatAssistantContentService.list("drawing_query_intent", "pdfAttachmentPhrases")
    assert ChatAssistantContentService.list("drawing_query_intent", "requiresPdfTerms")


def test_drawing_query_intent_direct_answers_from_json():
    assert "drawing-analysis-delpi" in ChatDrawingIntentService.build_skill_disabled_answer()
    assert "código delpi" in ChatDrawingIntentService.build_missing_pdf_answer().lower()
    assert "biblioteca" in ChatDrawingIntentService.build_missing_product_code_answer().lower()
    assert "90260140" in ChatDrawingIntentService.build_missing_product_code_answer()
    assert "90262957" in ChatDrawingIntentService.build_drawing_library_not_found_answer(
        "90262957"
    )


def test_conformidade_delpi_trigger_from_json_bundle():
    assert ChatDrawingIntentService.is_drawing_analysis_request(
        "gerar relatorio de conformidade delpi 90260140"
    )


def test_llm_fallback_policy_loaded_from_json():
    addon = ChatDrawingIntentService.build_llm_fallback_policy_addon(
        "Analise o desenho 90260140",
        attachment_ids=["att-1"],
    )

    assert "Relatório de Análise de Desenho DELPI" in addon
    assert "Não invente" in addon or "nao invente" in addon.lower()
