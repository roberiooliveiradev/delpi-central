from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_brief_direct_service import (
    ChatOperationalLlmSynthesisBriefDirectService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def _tool_calls(metadata: dict) -> list[dict]:
    return [{"name": "execute_external_action", "metadata": metadata}]


def test_fast_commentary_direct_builds_answer_without_llm():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "highlights": [{"text": "O produto **10080045** está cadastrado como MP."}],
            "attention": ["Roteiro sem operações registradas."],
        },
    }

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "me fale do produto 10080045",
        _tool_calls(metadata),
        response_mode="fast",
    )

    assert answer
    assert "10080045" in answer
    assert "MP" in answer


def test_apply_turn_direct_answer_policy_fast_uses_commentary_direct():
    tool_context: dict = {}
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "presentationDecision": {"layoutMode": "stack", "selected": "table"},
        "dataCommentary": {
            "highlights": [
                {"text": "O produto **10080045** está cadastrado como MP."},
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="fast",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct
    assert "10080045" in direct
    assert skip_rag is True
    assert effect == "llm_synthesis_brief"
    assert tool_context.get("commentaryBriefDirect") is True


def test_apply_turn_direct_answer_policy_fast_prefers_commentary_over_composite_direct():
    tool_context: dict = {}
    composite_direct = "### Status fabril\n\nProsa longa do presenter."
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/90260140/factory-status",
        "dataCommentary": {
            "highlights": [
                {
                    "text": (
                        "Status fabril **INTERMEDIÁRIOS EM PRODUÇÃO / PA NÃO FINALIZADO** "
                        "para o produto **90260140**."
                    ),
                },
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="Qual o status completo na fábrica do produto 90260140 hoje?",
        response_mode="fast",
        direct_answer=composite_direct,
        skip_rag=True,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct
    assert direct != composite_direct
    assert "90260140" in direct
    assert effect == "llm_synthesis_brief"
    assert tool_context.get("commentaryBriefDirect") is True


def test_normal_commentary_direct_disabled_returns_none():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "highlights": [
                {"text": "O produto **10080045** está cadastrado como MP."},
            ],
        },
    }

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "me fale do produto 10080045",
        _tool_calls(metadata),
        response_mode="normal",
    )

    assert answer is None


def test_apply_turn_direct_answer_policy_normal_uses_llm_not_commentary_direct():
    tool_context: dict = {}
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "highlights": [
                {"text": "O produto **10080045** está cadastrado como MP."},
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="normal",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct is None
    assert skip_rag is True
    assert effect == "llm_synthesis"
    assert tool_context.get("commentaryBriefDirect") is not True
