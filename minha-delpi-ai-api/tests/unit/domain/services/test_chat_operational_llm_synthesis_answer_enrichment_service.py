from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)

configure_domain_infrastructure_ports()


def _tool_calls(metadata: dict) -> list[dict]:
    return [{"name": "execute_external_action", "metadata": metadata}]


def test_prepends_product_code_when_missing_from_llm_answer():
    answer = "Produto cadastrado como MP com estrutura disponível no painel."

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis_brief",
    )

    assert "10080045" in enriched
    assert enriched.index("10080045") < 40


def test_keeps_answer_when_product_code_already_present():
    answer = "O produto **10080045** está cadastrado como MP."

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis",
    )

    assert enriched == answer


def test_strips_route_hallucination_when_attention_says_empty():
    answer = (
        "O produto **10080045** é MP. "
        "Há operações registradas no roteiro que não foram retornadas nesta consulta."
    )
    metadata = {
        "ok": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "attention": ["Roteiro sem operações registradas."],
        },
    }

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls(metadata),
        response_mode_effect="llm_synthesis_brief",
    )

    assert "10080045" in enriched
    assert "não foram retornadas" not in enriched.lower()
    assert "há operações registradas" not in enriched.lower()


def test_strips_markdown_tables_when_decoupled():
    answer = (
        "O produto **10080045** é MP.\n\n"
        "| Rota | Status |\n|------|--------|\n| /analyser | ok |\n\n"
        "Consulte o painel para detalhes."
    )

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "llmProseDecoupled": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis_brief",
    )

    assert "|" not in enriched
    assert "painel" in enriched.lower()


def test_skips_enrichment_without_llm_synthesis_effect():
    answer = "Resposta curta sem código."

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="direct_answer",
    )

    assert enriched == answer
