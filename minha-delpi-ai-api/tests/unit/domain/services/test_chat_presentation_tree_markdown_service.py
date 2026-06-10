from app.domain.services.chat_presentation_tree_markdown_service import (
    ChatPresentationTreeMarkdownService,
)


def _sample_tree_presentation() -> dict:
    return {
        "type": "tree",
        "title": "Estrutura do produto",
        "root": {
            "id": "90269001",
            "label": "90269001",
            "badge": "PA",
            "metaCaption": "1 MI",
            "subtitle": "ITEM RAIZ",
            "children": [
                {
                    "id": "C1",
                    "label": "C1",
                    "badge": "PI",
                    "metaCaption": "1 UN",
                    "subtitle": "COMPONENTE 1",
                    "children": [
                        {
                            "id": "C2",
                            "label": "C2",
                            "badge": "MP",
                            "metaCaption": "2 UN",
                            "subtitle": "SUBCOMPONENTE",
                        }
                    ],
                }
            ],
        },
    }


def test_outline_markdown_uses_ascii_tree_branches():
    outline = ChatPresentationTreeMarkdownService.outline_markdown(
        _sample_tree_presentation()
    )

    assert outline.startswith("90269001 PA 1 MI — ITEM RAIZ")
    assert "└── C1 PI 1 UN — COMPONENTE 1" in outline
    assert "    └── C2 MP 2 UN — SUBCOMPONENTE" in outline


def test_build_outline_section_wraps_in_code_fence():
    section = ChatPresentationTreeMarkdownService.build_outline_section(
        _sample_tree_presentation()
    )

    assert "**Composição**" in section
    assert "```text" in section
    assert "└── C1 PI 1 UN — COMPONENTE 1" in section


def test_embed_outline_in_text_presentation_when_text_selected():
    metadata = {
        "path": "/products/90269001/structure",
        "explicitSessionFormat": "text",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estrutura\n\nProduto **90269001**.",
        },
        "treePresentation": _sample_tree_presentation(),
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
        },
    }

    ChatPresentationTreeMarkdownService.embed_outline_in_text_presentation(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "└── C1 PI 1 UN — COMPONENTE 1" in markdown
    assert "A composição está na **árvore**" not in markdown


def test_embed_outline_runs_with_humanized_sections_when_profile_allows():
    metadata = {
        "path": "/products/90269001/structure",
        "explicitSessionFormat": "text",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estrutura\n\nResumo.",
        },
        "treePresentation": _sample_tree_presentation(),
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "stackPresentationPlan": {"humanizedSections": True},
        },
    }

    ChatPresentationTreeMarkdownService.embed_outline_in_text_presentation(metadata)

    assert "└── C1 PI 1 UN — COMPONENTE 1" in metadata["textPresentation"]["markdown"]


def test_embed_outline_skips_when_tree_is_primary():
    metadata = {
        "path": "/products/90269001/structure",
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estrutura\n\nResumo.",
        },
        "treePresentation": _sample_tree_presentation(),
        "presentation": _sample_tree_presentation(),
        "presentationDecision": {
            "selected": "tree",
            "layoutMode": "single",
        },
    }

    ChatPresentationTreeMarkdownService.embed_outline_in_text_presentation(metadata)

    assert "├──" not in metadata["textPresentation"]["markdown"]
