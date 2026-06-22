from app.application.services.chat_turn.chat_turn_preparation_post_tool_resolution_service import (
    ChatTurnPreparationPostToolResolutionService,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)


def _resolve_post_tool(**overrides):
    defaults = {
        "message": "me fale do produto 10080045",
        "workspace_context": {},
        "history_source": [],
        "pipeline_stages": [],
        "tool_context": {"directAnswer": "### Produto\n\nRelatório stack."},
        "tool_calls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "textPresentation": {
                        "type": "markdown",
                        "markdown": "### Produto\n\nRelatório stack.",
                    },
                    "presentationDecision": {
                        "layoutMode": "stack",
                        "visualOrder": ["text", "table"],
                    },
                },
            }
        ],
        "fast_path": False,
        "analysis_mode": False,
        "operational_optimize": False,
        "text_task_pure": False,
        "canvas_action": None,
        "pre_capability_answer": None,
        "small_talk_direct": None,
        "utility_direct": None,
        "web_post_search_direct": None,
        "web_save_sources_direct": None,
        "project_sources_direct": None,
        "attachment_welcome_direct": None,
        "session_memory_direct": None,
        "interpretation_without_data_answer": None,
        "unclear_direct": None,
        "missing_product_code_answer": None,
        "ambiguous_period_answer": None,
        "missing_date_answer": None,
        "common_chat_operational_answer": None,
        "routing_disambiguation_answer": None,
        "learning_term_confirmation_answer": None,
        "skip_tools_for_data_interpretation": False,
        "resolve_user_identity_answer": lambda _message: None,
        "resolve_capabilities_answer": lambda _message: None,
        "attachment_ids": None,
        "response_mode": "normal",
    }
    defaults.update(overrides)

    return ChatTurnPreparationPostToolResolutionService.resolve(**defaults)


def test_post_tool_overview_normal_clears_direct_answer_for_llm():
    result = _resolve_post_tool(response_mode="normal")

    assert result.direct_answer is None
    assert result.skip_rag is True
    assert result.tool_context.get("responseModeEffect") == "llm_synthesis"


def test_post_tool_overview_fast_clears_direct_answer_for_brief_llm():
    result = _resolve_post_tool(response_mode="fast")

    assert result.direct_answer is None
    assert result.skip_rag is True
    assert result.tool_context.get("responseModeEffect") == "llm_synthesis_brief"
    assert "directAnswer" not in result.tool_context


def test_post_tool_user_identity_routes_to_llm_not_direct_answer():
    profile = (
        "**Seu perfil na Minha DELPI:**\n\n"
        "- **Nome:** Robério Oliveira\n"
        "- **Email:** engenharia6@delpi.com.br"
    )
    result = _resolve_post_tool(
        message="quem sou eu?",
        pipeline_stages=["identity_shortcut"],
        tool_context={},
        tool_calls=[],
        resolve_user_identity_answer=lambda _message: profile,
        response_mode="normal",
    )

    assert result.direct_answer is None
    assert result.skip_rag is True
    assert result.tool_context.get(ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_LLM_SYNTHESIS)
    assert (
        result.tool_context.get(ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS)
        == profile
    )
    assert result.tool_context.get(ChatUserProfileLlmSynthesisService.TOOL_CONTEXT_SYNTHESIS_FLAG)
    assert result.tool_context.get("responseModeEffect") == "llm_synthesis"


def test_post_tool_capabilities_question_routes_to_llm_not_direct_answer():
    caps = (
        "Posso ajudar você nestes formatos:\n\n"
        "**Sempre disponíveis (chat comum e agentes)**\n"
        "- Respostas com base na documentação autorizada (RAG)."
    )
    result = _resolve_post_tool(
        message="o que você pode fazer?",
        pipeline_stages=[],
        tool_context={},
        tool_calls=[],
        resolve_capabilities_answer=lambda _message: caps,
        response_mode="normal",
    )

    assert result.direct_answer is None
    assert result.skip_rag is True
    assert caps in result.tool_context.get(
        ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS,
        "",
    )
    assert result.tool_context.get("responseModeEffect") == "llm_synthesis"


def test_post_tool_small_talk_keeps_direct_answer_with_llm_prose_everywhere():
    greeting = "Bom dia! Como posso ajudar?"
    result = _resolve_post_tool(
        message="bom dia",
        pipeline_stages=["small_talk"],
        tool_context={},
        tool_calls=[],
        small_talk_direct=greeting,
        response_mode="normal",
    )

    assert result.direct_answer == greeting
    assert result.skip_rag is True
    assert result.tool_context.get("responseModeEffect") == "simple_direct"


def test_post_tool_overview_fast_uses_commentary_direct_when_decoupled():
    result = _resolve_post_tool(
        response_mode="fast",
        tool_context={},
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "llmProseDecoupled": True,
                    "path": "/products/10080045/analyser",
                    "dataCommentary": {
                        "highlights": [
                            {"text": "O produto **10080045** está cadastrado como MP."},
                        ],
                    },
                    "presentationDecision": {
                        "layoutMode": "stack",
                        "visualOrder": ["text", "table"],
                    },
                },
            }
        ],
    )

    assert result.direct_answer
    assert "10080045" in result.direct_answer
    assert result.tool_context.get("commentaryBriefDirect") is True
    assert result.tool_context.get("responseModeEffect") == "llm_synthesis_brief"
