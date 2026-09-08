from app.domain.services.chat_prose_markdown_join_service import (
    ChatProseMarkdownJoinService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_answer_enrichment_service import (
    ChatOperationalLlmSynthesisAnswerEnrichmentService,
)

configure_domain_infrastructure_ports()


def test_join_preserves_heading_and_list_after_sentence_split():
    fragments = [
        "qualquer necessidade dependeria de reposição antes do atendimento.",
        "## Estrutura (BOM)",
        "A composição tem 6 componentes.",
        "- **2 matérias-primas são reutilizadas** em mais de um intermediário.",
        "- **3 intermediários têm variação de cor** na descrição.",
    ]

    joined = ChatProseMarkdownJoinService.join_sentence_fragments(fragments)

    assert "\n\n## Estrutura (BOM)\n\n" in joined or joined.index("## Estrutura") > joined.index(
        "atendimento."
    )
    assert "\n\n- **2 matérias-primas" in joined
    assert "\n\n- **3 intermediários" in joined
    assert ". ## " not in joined
    assert ". - **" not in joined


def test_finalize_preserves_markdown_blocks_for_c4_style_prose():
    answer = (
        "O produto **90260149** está sem estoque e o estoque não cobre demanda típica: "
        "qualquer necessidade dependeria de reposição antes do atendimento.\n\n"
        "## Estrutura (BOM)\n\n"
        "A composição tem **6 componentes**.\n\n"
        "- **2 matérias-primas são reutilizadas** em mais de um intermediário.\n"
        "- **3 intermediários têm variação de cor** na descrição.\n\n"
        "## Estoque\n\n"
        "A posição consultada está zerada."
    )

    enriched = ChatOperationalLlmSynthesisAnswerEnrichmentService.finalize_answer(
        answer,
        message="estrutura e se o estoque cobre demanda do 90260149",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/90260149/structure",
                    "llmProseDecoupled": True,
                },
            },
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/90260149/stock",
                    "llmProseDecoupled": True,
                    "presentation": {
                        "type": "table",
                        "rows": [{"available_quantity": 0}],
                    },
                },
            },
        ],
        response_mode_effect="llm_synthesis",
        response_mode="normal",
    )

    assert "\n## Estrutura (BOM)\n" in enriched or "\n\n## Estrutura (BOM)\n" in enriched
    assert ". ## " not in enriched
    assert ". - **" not in enriched
    assert "- **2 matérias-primas" in enriched
    assert "- **3 intermediários" in enriched
