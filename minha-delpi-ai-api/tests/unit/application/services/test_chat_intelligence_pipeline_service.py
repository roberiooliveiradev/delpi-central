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


def test_resolve_analysis_direct_answer_with_history():
    messages = [
        {"role": "user", "content": "estrutura do 90260077"},
        {
            "role": "assistant",
            "content": "Estrutura do produto\n50230002 — X (PI) [MI] | Qtd: 1.0",
            "metadata": {},
        },
        {"role": "user", "content": "estrutura do 90260088"},
        {
            "role": "assistant",
            "content": "Estrutura do produto\n50210053 — Y (PI) [MI] | Qtd: 1.0",
            "metadata": {},
        },
    ]
    answer = ChatIntelligencePipelineService.resolve_analysis_direct_answer(
        "compare as duas estruturas",
        messages,
    )
    assert answer
    assert "90260077" in answer


def test_pre_tool_decisions_enable_operational_fast_path_on_stock_refinement():
    messages = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                        },
                    }
                ]
            },
        },
    ]

    decisions = ChatIntelligencePipelineService.resolve_pre_tool_decisions(
        "filtre filial 02",
        ["stock-action"],
        previous_messages=messages,
    )

    assert decisions.operational_optimize
    assert not decisions.analysis_mode


def test_resolve_direct_answer_returns_none_in_analysis_mode():
    answer = ChatIntelligencePipelineService.resolve_direct_answer(
        {"directAnswer": "resposta operacional"},
        analysis_mode=True,
    )

    assert answer is None


def test_finalize_after_tools_enriches_document_vision_context():
    post = ChatIntelligencePipelineService.finalize_after_tools(
        "descreva a imagem anexada",
        [],
        {
            "context": "",
            "toolCalls": [],
            "documentVision": {
                "imageDescription": "Painel com três botões verdes.",
                "textExcerpt": "REV. 02",
                "filename": "desenho.png",
            },
        },
    )

    context = post.tool_context.get("context", "")

    assert "Descrição visual" in context
    assert "Painel com três botões" in context
    assert "REV. 02" in context
