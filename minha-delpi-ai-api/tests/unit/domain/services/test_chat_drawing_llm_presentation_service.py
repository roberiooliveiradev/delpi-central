from app.domain.services.chat_drawing_llm_presentation_service import (
    ChatDrawingLlmPresentationService,
)
from app.domain.services.prompt_policy_service import PromptPolicyService


def _history_with_analysis() -> list[dict]:
    return [
        {
            "role": "assistant",
            "metadata": {
                "drawingAnalysis": {
                    "productCode": "90262008",
                    "items": [
                        {
                            "item": "Revisão",
                            "status": "ok",
                            "templateKey": "revision_cross_ok",
                        }
                    ],
                }
            },
        }
    ]


def test_hydrates_drawing_analysis_on_follow_up_without_new_analysis_request():
    hydrated = ChatDrawingLlmPresentationService.hydrate_tool_context(
        {"context": "tool result"},
        message="explique o erro do conector no relatório anterior",
        attachment_ids=None,
        previous_messages=_history_with_analysis(),
    )

    assert hydrated.get("drawingAnalysisMode") is True
    assert hydrated["drawingAnalysis"]["productCode"] == "90262008"


def test_skips_hydration_on_new_drawing_analysis_request():
    hydrated = ChatDrawingLlmPresentationService.hydrate_tool_context(
        {"context": ""},
        message="analise o desenho 90262008",
        attachment_ids=["att-1"],
        previous_messages=_history_with_analysis(),
    )

    assert "drawingAnalysis" not in hydrated


def test_enrich_context_string_includes_drawing_analysis_marker():
    tool_context = {
        "drawingAnalysisMode": True,
        "drawingAnalysis": _history_with_analysis()[0]["metadata"]["drawingAnalysis"],
    }

    enriched = ChatDrawingLlmPresentationService.enrich_context_string(
        "execute_external_action ok",
        tool_context,
    )

    assert "drawingAnalysisMode" in enriched
    assert "revision_cross_ok" in enriched


def test_follow_up_policy_addon_loads_render_only():
    addon = ChatDrawingLlmPresentationService.build_llm_policy_addon(
        message="qual o plano de ação para corrigir o desenho?",
        attachment_ids=None,
        tool_context={"context": ""},
        previous_messages=_history_with_analysis(),
    )

    assert "Modo render-only" in addon


def test_contextual_prompt_includes_render_only_after_follow_up_hydration():
    service = PromptPolicyService()
    tool_context = ChatDrawingLlmPresentationService.hydrate_tool_context(
        {"context": ""},
        message="resuma os pontos de atenção do desenho",
        attachment_ids=None,
        previous_messages=_history_with_analysis(),
    )
    context = ChatDrawingLlmPresentationService.enrich_context_string(
        str(tool_context.get("context") or ""),
        tool_context,
    )

    prompt = service.build_contextual_prompt(
        rag_context="",
        tool_context=context,
        skills={"drawingAnalysis": True},
    )

    assert "Modo render-only" in prompt
    assert "drawingAnalysis" in prompt
