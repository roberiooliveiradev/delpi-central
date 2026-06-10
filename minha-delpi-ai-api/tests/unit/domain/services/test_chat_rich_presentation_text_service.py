from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)


def _metadata_with_stack(*, markdown: str) -> dict:
    return {
        "ok": True,
        "textPresentation": {
            "type": "markdown",
            "markdown": markdown,
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Estoque",
                "columns": [{"key": "branch", "label": "Filial"}],
                "rows": [{"branch": "01"}],
            }
        ],
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "title": "Saldo",
            "data": [{"branch": "01", "qty": 1}],
        },
        "presentationDecision": {
            "layoutMode": "stack",
            "availableViews": ["text", "table", "chart"],
            "visualOrder": ["text", "table", "chart"],
        },
    }


def test_compact_metadata_strips_stock_position_detail_when_table_exists():
    markdown = (
        "### Estoque\n\n"
        "Resumo com 5 posições.\n\n"
        "**Detalhamento por filial e armazém**\n\n"
        "- Filial 01, armazém 01: atual 10, disponível 8, empenhada 0.\n"
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    compact = metadata["textPresentation"]["markdown"]

    assert "Detalhamento por filial" not in compact
    assert "Filial 01, armazém 01" not in compact
    assert "Resumo com 5 posições" in compact


def test_compact_metadata_removes_markdown_table_and_footer():
    markdown = (
        "### Estoque\n\n"
        "| Filial | Qtd |\n| --- | --- |\n| 01 | 10 |\n\n"
        "Use a **tabela** abaixo para conferir.\n\n"
        "**Destaques**\n\n- Saldo positivo."
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    compact = metadata["textPresentation"]["markdown"]

    assert "| Filial |" not in compact
    assert "Use a **tabela**" not in compact
    assert "**Destaques**" in compact


def test_should_prefer_authorized_answer_for_any_stack_tool_call():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": _metadata_with_stack(markdown="**Destaques**\n\n- Item."),
        }
    ]

    assert ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
        tool_calls
    )


def test_embed_visual_markers_for_analyser_sections():
    markdown = (
        "### Informações completas do produto 90260149\n\n"
        "**Destaques**\n\n"
        "- Estrutura com 6 itens.\n\n"
        "**Pontos de atenção encontrados na API:**\n\n"
        "1. Bloqueio «2»."
    )
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {"type": "markdown", "markdown": markdown},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Roteiro de produção — 90260149",
                "columns": [],
                "rows": [],
            },
            {
                "type": "table",
                "title": "Produto 90260149",
                "columns": [],
                "rows": [],
            },
        ],
        "presentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "90260149", "label": "90260149", "children": []},
        },
        "presentationDecision": {
            "layoutMode": "stack",
            "availableViews": ["text", "table", "tree"],
        },
    }

    embedded = ChatRichPresentationTextService.embed_visual_markers_in_markdown(
        markdown,
        metadata,
    )

    assert "[[table:1]]" not in embedded
    assert "[[table:2]]" not in embedded
    assert "[[arvore]]" not in embedded


def test_compact_metadata_stack_skips_embedded_markers():
    markdown = (
        "### Estoque do produto\n\n"
        "Posição de estoque do produto **90260149**.\n\n"
        "[[table:1]]\n\n[[chart]]"
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    compact = metadata["textPresentation"]["markdown"]

    assert "[[table:" not in compact
    assert "[[chart]]" not in compact


def test_compact_metadata_humanized_analyser_without_markers():
    markdown = (
        "### Informações completas do produto 90260149\n\n"
        "**Destaques**\n\n- Estrutura com 6 itens."
    )
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {"type": "markdown", "markdown": markdown},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Produto 90260149",
                "columns": [{"key": "campo", "label": "Campo"}],
                "rows": [{"campo": "Código", "valor": "90260149"}],
            },
        ],
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "nodes": [{"id": "1", "label": "90260149"}],
        },
        "stackPresentationPlan": {
            "humanizedSections": True,
            "presentationProfile": "product_analyser",
        },
        "presentationDecision": {"layoutMode": "stack"},
    }

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    assert "[[table:" not in metadata["textPresentation"]["markdown"]
    assert "[[arvore]]" not in metadata["textPresentation"]["markdown"]


def test_should_compact_narrative_for_table_plus_tree():
    assert ChatRichPresentationTextService.should_compact_narrative(
        table_presentations=[{"type": "table", "title": "Cadastro", "columns": [], "rows": []}],
        tree_presentation={
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "1", "label": "1", "children": []},
        },
    )
