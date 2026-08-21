from app.domain.services.chat_intent_router.chat_intent_router_classify_service import (
    ChatIntentRouterClassifyService,
)
from app.domain.services.chat_presentation_prose_delivery_content_service import (
    ChatPresentationProseDeliveryContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


def test_preserve_direct_answer_stages_include_drawing():
    stages = ChatPresentationProseDeliveryContentService.preserve_direct_answer_stages()

    assert "drawing_analysis" in stages
    assert "drawing_report_adjustment" in stages


def test_drawing_analysis_stage_preserves_direct_answer_under_llm_everywhere():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="confirmar revisão manual do item pendente",
        response_mode="normal",
        direct_answer="Relatório já revisado.",
        skip_rag=True,
        tool_calls=[],
        tool_context={"drawingAnalysisMode": True},
        pipeline_stages=["drawing_analysis", "drawing_report_adjustment"],
    )

    assert direct == "Relatório já revisado."
    assert effect == "simple_direct"
    assert skip_rag is True


def test_intent_router_classifies_drawing_report_adjustment():
    result = ChatIntentRouterClassifyService.classify(
        "confirmar revisão manual do item pendente no relatório do desenho 90261899",
    )

    assert result.intent == "drawing_report_adjustment"
    assert result.requires_llm is False
    assert result.requires_tool is False
