"""Testes do loader de marcadores do stack markdown."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_presentation_stack_markdown_content_service import (
    ChatPresentationStackMarkdownContentService,
)


def test_stack_markdown_markers_load_from_presenter_content():
    assert ChatPresentationStackMarkdownContentService.highlights_header() == "**Destaques**"
    assert ChatPresentationStackMarkdownContentService.attention_header_prefix().startswith(
        "**Pontos de atenção"
    )
    assert ChatPresentationStackMarkdownContentService.compile_pattern(
        "highlightsHeaderLine"
    ).search("**Destaques**")
    assert ChatPresentationStackMarkdownContentService.compile_pattern(
        "attentionNumberedItem"
    ).search("1. Algo")
