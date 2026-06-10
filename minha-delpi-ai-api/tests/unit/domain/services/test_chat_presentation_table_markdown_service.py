from app.domain.services.chat_presentation_table_markdown_service import (
    ChatPresentationTableMarkdownService,
)


def _sample_table(title: str = "Panorama fabril") -> dict:
    return {
        "type": "table",
        "title": title,
        "role": "profile",
        "columns": [
            {"key": "campo", "label": "Campo"},
            {"key": "valor", "label": "Valor"},
        ],
        "rows": [
            {"campo": "Situação consolidada", "valor": "PA PRODUZIDO"},
            {"campo": "Produto", "valor": "90269002"},
        ],
    }


def test_build_table_section_renders_markdown_pipe_table():
    section = ChatPresentationTableMarkdownService._table_section(_sample_table())

    assert "**Panorama fabril**" in section
    assert "| Campo | Valor |" in section
    assert "PA PRODUZIDO" in section


def test_embed_tables_in_text_presentation_when_text_selected():
    metadata = {
        "path": "/products/90269002/factory-status",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nResumo operacional.",
        },
        "tablePresentations": [_sample_table()],
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
        },
    }

    ChatPresentationTableMarkdownService.embed_tables_in_text_presentation(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "| Campo | Valor |" in markdown
    assert "PA PRODUZIDO" in markdown


def test_embed_tables_skips_stack_layout():
    metadata = {
        "path": "/products/90269002/factory-status",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nResumo.",
        },
        "tablePresentations": [_sample_table()],
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
    }

    ChatPresentationTableMarkdownService.embed_tables_in_text_presentation(metadata)

    assert "| Campo | Valor |" not in metadata["textPresentation"]["markdown"]
