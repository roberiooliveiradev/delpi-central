from app.domain.services.chat_assistant_markdown_structure_service import (
    ChatAssistantMarkdownStructureService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_turn_finalization_service import (
    ChatOperationalLlmSynthesisTurnFinalizationService,
)

configure_domain_infrastructure_ports()


def test_normalize_breaks_inline_atx_heading_after_period():
    raw = (
        "o estoque atual **não cobre** uma demanda típica. ## Cadastro e estoque\n\n"
        "O produto é um chicote."
    )

    out = ChatAssistantMarkdownStructureService.normalize_delivered_markdown(raw)

    assert ". ## " not in out
    assert "típica.\n\n## Cadastro e estoque\n\n" in out
    assert not ChatAssistantMarkdownStructureService.has_inline_block_marker(out)


def test_normalize_breaks_inline_heading_after_em_dash_without_space():
    raw = "O produto **90260149** —## Cadastro e estoque\n\nO item é um chicote."

    out = ChatAssistantMarkdownStructureService.normalize_delivered_markdown(raw)

    assert "—##" not in out
    assert "—\n\n## Cadastro e estoque\n\n" in out
    assert not ChatAssistantMarkdownStructureService.has_inline_block_marker(out)


def test_normalize_sibling_colon_and_list_inline():
    raw = (
        "Resumo do item: ## Estrutura (BOM)\n"
        "A composição tem 6 componentes. - **2 matérias-primas** repetem."
    )

    out = ChatAssistantMarkdownStructureService.normalize_delivered_markdown(raw)

    assert ": ## " not in out
    assert ". - **" not in out
    assert "\n\n## Estrutura (BOM)\n" in out
    assert "\n\n- **2 matérias-primas**" in out


def test_normalize_negative_preserves_valid_markdown_and_fences():
    raw = (
        "Abertura do produto.\n\n"
        "## Cadastro e estoque\n\n"
        "Texto válido.\n\n"
        "```sql\nSELECT 1 AS n -- ## not a heading\n```\n\n"
        "- item A\n"
        "- item B"
    )

    out = ChatAssistantMarkdownStructureService.normalize_delivered_markdown(raw)

    assert out == raw.strip()
    assert "```sql\nSELECT 1 AS n -- ## not a heading\n```" in out
    assert not ChatAssistantMarkdownStructureService.has_inline_block_marker(out)


def test_finalize_persisted_answer_normalizes_c4_style_inline_headings():
    raw = (
        "Visão consolidada do produto **90260149**. "
        "Estoque **não cobre** demanda típica. ## Cadastro e estoque\n\n"
        "O produto é um chicote. ## Estrutura (BOM)\n\n"
        "A composição tem 6 componentes."
    )
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/90260149/structure",
                "presentationDecision": {
                    "proseSource": "llm",
                    "proseCompositionPolicy": "api_only",
                },
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/90260149/stock",
            },
        },
    ]

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        raw,
        tool_calls,
        message="completa estrutura e estoque 90260149",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert ". ## " not in result
    assert "\n## Cadastro e estoque\n" in result or "\n\n## Cadastro e estoque\n" in result
    assert "\n## Estrutura (BOM)\n" in result or "\n\n## Estrutura (BOM)\n" in result
    assert not ChatAssistantMarkdownStructureService.has_inline_block_marker(result)
