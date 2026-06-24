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


def test_strips_hallucination_markers_from_llm_answer():
    answer = (
        "O produto **10080045** é MP do grupo 1008. "
        "Trata-se de um componente de engrenagem 2D usado na operação de preparo."
    )
    metadata = {
        "ok": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "highlights": [{"text": "O produto **10080045** está cadastrado como MP."}],
        },
    }

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls(metadata),
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in enriched
    assert "engrenagem" not in enriched.lower()


def test_dedupes_repeated_paragraphs():
    paragraph = (
        "O produto **10080045** está cadastrado como MP. "
        "O painel traz cadastro, estrutura e roteiro."
    )
    answer = f"{paragraph}\n\n{paragraph}"

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis",
    )

    assert enriched.count("10080045") == 1


def test_trims_normal_prose_to_budget():
    answer = "O produto **10080045** " + ("é MP. " * 120)

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis",
        response_mode="normal",
    )

    assert len(enriched) <= 521


def test_dedupes_repeated_markdown_sections_for_thinker():
    answer = (
        "### Destaques\n\n"
        "O produto **10080045** está cadastrado como MP.\n\n"
        "### Destaques\n\n"
        "O produto **10080045** está cadastrado como MP.\n\n"
        "### Pontos de atenção\n\n"
        "Roteiro sem operações registradas."
    )

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="me fale do produto 10080045",
        tool_calls=_tool_calls({"ok": True, "path": "/products/10080045/analyser"}),
        response_mode_effect="llm_synthesis",
        response_mode="thinker",
    )

    assert enriched.count("### Destaques") == 1
    assert "### Pontos de atenção" in enriched


def test_strips_exclusivity_contradiction_when_zero_exclusive_mps():
    answer = (
        "O produto 90260882 tem a exclusividade definida por 3 matérias-primas "
        "compartilhadas com outros PAs."
    )
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260882/structure/exclusivity",
                "kpiPresentation": {
                    "metrics": [
                        {"label": "MPs exclusivas", "value": "0"},
                    ],
                },
            },
        }
    ]

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="quais MPs exclusivas tem o produto 90260882?",
        tool_calls=tool_calls,
        response_mode_effect="llm_synthesis",
        response_mode="normal",
    )

    assert enriched == "" or "exclusividade definida" not in enriched.lower()
