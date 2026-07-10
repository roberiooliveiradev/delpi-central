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


def test_report_adjustment_triggers_loaded_from_json():
    from app.domain.services.chat_drawing_query_intent_content_service import (
        ChatDrawingQueryIntentContentService,
    )

    assert ChatDrawingQueryIntentContentService.list_values(
        "reportAdjustmentTriggers",
        "confirmManual",
    )
    assert ChatDrawingQueryIntentContentService.get(
        "directAnswers",
        "ambiguousAdjustment",
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


def test_follow_up_render_only_policy_configured():
    policy_file = ChatAssistantContentService.get(
        "drawing_query_intent",
        "followUpRenderOnly",
        "policyFile",
    )

    assert policy_file == "drawing-analysis-render-only.md"


def test_rag_normative_policy_configured():
    policy_file = ChatAssistantContentService.get(
        "drawing_query_intent",
        "ragNormative",
        "policyFile",
    )

    assert policy_file == "drawing-analysis-rag-normative.md"


def test_unit_conversion_policy_configured():
    policy_file = ChatAssistantContentService.get(
        "drawing_query_intent",
        "unitConversion",
        "policyFile",
    )
    rag_source = ChatAssistantContentService.get(
        "drawing_query_intent",
        "unitConversion",
        "ragSource",
    )

    assert policy_file == "drawing-analysis-unit-conversion.md"
    assert rag_source == "produto-conversao-unidades-protheus.txt"


def test_agent_knowledge_sources_configured():
    sources = ChatAssistantContentService.get_node(
        "drawing_query_intent",
        "agentKnowledgeSources",
    )

    assert isinstance(sources, list) and sources
    assert any(
        isinstance(item, dict)
        and item.get("sourceFile") == "produto-conversao-unidades-protheus.txt"
        for item in sources
    )


def test_drawing_analysis_rag_query_suffix_from_json():
    from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

    query = ChatDrawingIntentService.build_rag_query("validar desenho 90262008")

    assert "90262008" in query
    assert "B1_CONV" in query
    assert "produto-conversao-unidades" in query
