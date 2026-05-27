from types import SimpleNamespace

from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)


def test_pre_tool_decisions_disable_operational_fast_path_on_comparison():
    decisions = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
        "compare as duas estruturas e traga insights",
        ["product-structure"],
    )

    assert decisions.analysis_mode
    assert not decisions.operational_optimize
    assert not ChatOperationalPipelineService.should_optimize(
        "compare as duas estruturas e traga insights",
        ["product-structure"],
    )


def test_finalize_after_tools_enriches_context_from_history():
    messages = [
        SimpleNamespace(
            role="assistant",
            content="Estrutura",
            metadata={
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260077/structure",
                            "responsePreview": '{"code": "50230002"}',
                        },
                    }
                ]
            },
        ),
    ]

    post = ChatIntelligencePipelineService.finalize_after_tools(
        "compare as duas estruturas",
        messages,
        {"context": "", "toolCalls": []},
    )

    assert post.analysis_mode
    assert "90260077" in post.tool_context.get("context", "")
    assert post.tool_context.get("analysisMode") is True


def test_resolve_direct_answer_returns_none_in_analysis_mode():
    answer = ChatIntelligencePipelineService.resolve_direct_answer(
        {"directAnswer": "resposta operacional"},
        analysis_mode=True,
    )

    assert answer is None
