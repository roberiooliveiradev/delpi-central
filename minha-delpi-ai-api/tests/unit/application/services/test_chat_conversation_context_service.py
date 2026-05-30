from types import SimpleNamespace

from app.application.services.chat_conversation_context_service import (
    ChatConversationContextService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_build_analysis_context_includes_tool_preview():
    messages = [
        SimpleNamespace(
            role="user",
            content="estrutura do 90260077",
            metadata={},
        ),
        SimpleNamespace(
            role="assistant",
            content="Estrutura do produto",
            metadata={
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260077/structure",
                            "actionId": "product-structure",
                            "responsePreview": '{"items": [{"code": "50230002"}]}',
                        },
                    }
                ]
            },
        ),
    ]

    context = ChatConversationContextService.build_analysis_context(messages)

    assert "90260077" in context
    assert "50230002" in context
    assert "análise comparativa" in context.lower()


def test_apply_analysis_mode_clears_direct_answer_for_data_interpretation():
    tool_context = {
        "context": "",
        "directAnswer": "tabela repetida",
        "toolCalls": [],
    }
    history = [
        {
            "role": "assistant",
            "content": "Roteiro do produto",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260142/guide",
                            "responsePreview": '{"items": []}',
                        },
                    }
                ]
            },
        }
    ]

    analysis_mode, updated = ChatConversationContextService.apply_analysis_mode(
        "explique os dados acima",
        history,
        tool_context,
    )

    assert analysis_mode
    assert updated.get("directAnswer") is None
    assert updated.get("analysisMode") is True
    assert "interpretar os dados" in updated.get("context", "").lower()


def test_apply_analysis_mode_clears_direct_answer():
    tool_context = {
        "context": "",
        "directAnswer": "tabela repetida",
        "toolCalls": [],
    }

    analysis_mode, updated = ChatConversationContextService.apply_analysis_mode(
        "compare as duas estruturas e traga insights",
        [],
        tool_context,
    )

    assert analysis_mode
    assert updated.get("directAnswer") is None
    assert updated.get("analysisMode") is True


def test_operational_pipeline_skips_optimize_for_comparison():
    from app.domain.services.chat_operational_pipeline_service import (
        ChatOperationalPipelineService,
    )

    assert not ChatOperationalPipelineService.should_optimize(
        "compare as duas estruturas e traga insights",
        ["product-structure"],
    )


def test_comparison_message_matches_intent_helper():
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "comparar as duas estruturas e traga insights"
    )
