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


def test_compact_metadata_preserves_stock_narrative_when_visuals_exist():
    markdown = (
        "### Estoque\n\n"
        "Resumo com 5 posições.\n\n"
        "**Detalhamento por filial e armazém**\n\n"
        "- Filial 01, armazém 01: atual 10, disponível 8, empenhada 0.\n"
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    assert metadata["textPresentation"]["markdown"] == markdown


def test_compact_metadata_preserves_markdown_with_tables_and_footer():
    markdown = (
        "### Estoque\n\n"
        "| Filial | Qtd |\n| --- | --- |\n| 01 | 10 |\n\n"
        "Use a **tabela** abaixo para conferir.\n\n"
        "**Destaques**\n\n- Saldo positivo."
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    assert metadata["textPresentation"]["markdown"] == markdown


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


def test_should_prefer_authorized_answer_for_playbook_operational_humanized():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/production/consumption/top-items-validated",
                "apiDelpiResponseMeta": {
                    "entity": "production_consumption_top_items_validated",
                },
                "humanizedSummary": {
                    "titulo": "Consumo validado por apontamento",
                    "linhas": ["- MP 01010001", "- MP 01010002"],
                },
            },
        }
    ]

    assert ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
        tool_calls
    )


def test_should_not_prefer_authorized_markdown_for_single_table_layout():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "textPresentation": {
                    "type": "markdown",
                    "markdown": "### Estoque\n\n- Filial 01",
                },
                "presentation": {
                    "type": "table",
                    "title": "Estoque",
                    "columns": [{"key": "branch", "label": "Filial"}],
                    "rows": [{"branch": "01"}],
                },
                "presentationDecision": {
                    "selected": "table",
                    "layoutMode": "single",
                    "visualOrder": ["table"],
                },
            },
        }
    ]

    assert not ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
        tool_calls
    )


def test_should_not_persist_authorized_markdown_for_single_table_layout():
    from app.domain.services.chat_tool_context_presentation_service import (
        ChatToolContextPresentationService,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080001/stock",
                "textPresentation": {
                    "type": "markdown",
                    "markdown": "### Estoque\n\n**Stock:** page: 1, items: [{'branch': '01'}]",
                },
                "presentation": {
                    "type": "table",
                    "title": "Estoque do produto 10080001",
                    "columns": [{"key": "branch", "label": "Filial"}],
                    "rows": [{"branch": "01"}],
                },
                "presentationDecision": {
                    "selected": "table",
                    "layoutMode": "single",
                    "visualOrder": ["table"],
                },
            },
        }
    ]

    assert not ChatToolContextPresentationService.should_persist_authorized_tool_answer(
        tool_calls,
    )

    persisted = ChatToolContextPresentationService.resolve_authorized_persisted_answer(
        "Estoque do produto 10080001",
        tool_calls,
    )

    assert persisted == "Estoque do produto 10080001"
    assert "items:" not in persisted.lower()


def test_is_stack_layout_false_for_single_table_with_latent_views():
    metadata = {
        "presentation": {"type": "table", "title": "Estoque", "rows": []},
        "textPresentation": {"type": "markdown", "markdown": "### Estoque\n\nResumo."},
        "presentationDecision": {
            "selected": "table",
            "layoutMode": "single",
            "availableViews": ["text", "table", "chart"],
        },
    }

    assert not ChatRichPresentationTextService.is_stack_layout(metadata)
    assert not ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
        [{"name": "execute_external_action", "metadata": {**metadata, "ok": True}}],
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


def test_compact_metadata_stack_preserves_embedded_markers():
    markdown = (
        "### Estoque do produto\n\n"
        "Posição de estoque do produto **90260149**.\n\n"
        "[[table:1]]\n\n[[chart]]"
    )
    metadata = _metadata_with_stack(markdown=markdown)

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    assert metadata["textPresentation"]["markdown"] == markdown


def test_compact_metadata_skips_humanized_mp_price_narrative():
    markdown = (
        "### Análise de preço da matéria-prima — 10080001\n\n"
        "**Resumo do produto**\n"
        "Produto: **10080001**\n\n"
        "**Leitura do histórico**\n"
        "Faixa entre **R$ 0,08** e **R$ 0,09**.\n\n"
        "**Pontos de atenção**\n"
        "1. Cadastro defasado.\n"
    )
    metadata = {
        "path": "/products/10080001/raw-material-price-intelligence",
        "textPresentation": {"type": "markdown", "markdown": markdown},
        "tablePresentations": [{"type": "table", "title": "Panorama", "columns": [], "rows": []}],
        "treePresentation": {"type": "tree", "title": "Fornecedores", "root": {"id": "1", "children": []}},
        "kpiPresentation": {"type": "kpi", "title": "KPI", "cards": []},
        "stackPresentationPlan": {
            "humanizedSections": True,
            "presentationProfile": "product_raw_material_price_intelligence",
        },
    }

    ChatRichPresentationTextService.compact_metadata_text(metadata)

    compact = metadata["textPresentation"]["markdown"]

    assert "Leitura do histórico" in compact
    assert "Pontos de atenção" in compact
    assert compact == markdown


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


def test_should_compact_narrative_disabled_for_humanized_stack():
    assert not ChatRichPresentationTextService.should_compact_narrative(
        table_presentations=[{"type": "table", "title": "Cadastro", "columns": [], "rows": []}],
        tree_presentation={
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "1", "label": "1", "children": []},
        },
    )


def test_strip_data_answer_quick_layers_removes_resumo_and_status():
    markdown = (
        "### Status fabril\n\n"
        "<!-- section:scope -->\n\n"
        "Situação consolidada.\n\n"
        "**Resumo**\n\n"
        "Leitura repetida.\n\n"
        "Status geral: **OK** — sem bloqueio.\n\n"
        "<!-- section:guide -->\n\n"
        "Produção no período."
    )

    stripped = ChatRichPresentationTextService.strip_data_answer_quick_layers(markdown)

    assert "**Resumo**" not in stripped
    assert "Status geral:" not in stripped
    assert "Produção no período." in stripped


def test_prepare_evidence_first_chat_narrative_strips_embedded_visuals_in_stack_auto():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "textPresentation": {
            "markdown": (
                "### Status fabril\n\n"
                "Situação consolidada: **PA PRODUZIDO**\n\n"
                "**Composição**\n\n"
                "```text\n"
                "Produto 90262404\n"
                "└── 10160001 (MP)\n"
                "```\n\n"
                "**Panorama fabril**\n\n"
                "| Campo | Valor |\n"
                "| --- | --- |\n"
                "| Situação | OK |\n\n"
                "**Saldo de MP — 90262404**\n\n"
                "_Dados do gráfico (horizontal_bar) em tabela — visualização Mermaid não disponível._\n\n"
                "| name | Saldo |\n"
                "| --- | --- |\n"
                "| 10160001 | 6082 |"
            ),
        },
    }

    ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "PA PRODUZIDO" in markdown
    assert "Composição" not in markdown
    assert "```text" not in markdown
    assert "Panorama fabril" not in markdown
    assert "Dados do gráfico" not in markdown
    assert "| name |" not in markdown


def test_prepare_evidence_first_chat_narrative_strips_embedded_visuals_in_single_auto():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "single",
        },
        "textPresentation": {
            "markdown": (
                "### Status produtivo\n\n"
                "OP em andamento.\n\n"
                "| Campo | Valor |\n"
                "| --- | --- |\n"
                "| OPs de PA | 1 |"
            ),
        },
    }

    ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "OP em andamento" in markdown
    assert "| --- |" not in markdown


def test_prepare_evidence_first_chat_narrative_aligns_stock_with_data_answer():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "single",
        },
        "dataAnswer": {
            "profileKey": "stock",
            "summary": {
                "answer": "Saldo disponível total: **150** un. em **2** posição(ões).",
                "meaning": "Maior concentração na filial **01** (105 un. disponíveis).",
                "riskLevel": "ok",
            },
        },
        "textPresentation": {
            "markdown": (
                "### Estoque do produto — 90269001\n\n"
                "<!-- section:scope -->\n\n"
                "Posições de estoque por filial e armazém — saldo atual, disponível e empenhado.\n\n"
                "Consultei o estoque do produto **90269001**: **2** posição(ões) em **2** filial(is) "
                "(01, 02) e **1** armazém(ns) (01). No total, há **150** unidade(s) disponível(is) "
                "nesta consulta.\n\n"
                "**Detalhamento por filial e armazém**\n"
                "- Filial 01, armazém 01: atual 120, disponível 105."
            ),
        },
    }

    ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "Consultei o estoque" not in markdown
    assert "Saldo disponível total: **150** un." in markdown
    assert "Maior concentração na filial **01**" in markdown
    assert "**Detalhamento por filial e armazém**" in markdown


def test_prepare_evidence_first_chat_narrative_keeps_prose_strips_duplicates():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "textPresentation": {
            "markdown": (
                "### Status fabril\n\n"
                "Situação consolidada: **PA PRODUZIDO**\n\n"
                "**Resumo**\n\n"
                "Repetido.\n\n"
                "**Destaques**\n\n"
                "- Produção em andamento."
            ),
        },
    }

    ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "PA PRODUZIDO" in markdown
    assert "**Resumo**" not in markdown
    assert "**Destaques**" not in markdown


def test_build_scope_only_narrative_keeps_framing_and_guide():
    markdown = (
        "### Status fabril\n\n"
        "<!-- section:scope -->\n\n"
        "Situação consolidada: **PA PRODUZIDO**\n\n"
        "Referência da consulta: **20260610**\n\n"
        "**Resumo**\n\n"
        "Leitura repetida.\n\n"
        "<!-- section:profile -->\n\n"
        "**Panorama fabril**\n\n"
        "- Campo: valor\n\n"
        "<!-- section:guide -->\n\n"
        "Saldo de MPs frente à necessidade."
    )
    framing = "Status integrado na fábrica — estrutura, estoque, produção e expedição."

    compact = ChatRichPresentationTextService.build_scope_only_narrative(
        markdown,
        framing=framing,
    )

    assert framing in compact
    assert "Referência da consulta" not in compact
    assert "**Resumo**" not in compact
    assert "**Panorama fabril**" not in compact
    assert "<!-- section:guide -->" in compact
    assert "Saldo de MPs frente à necessidade." in compact


def test_prepare_evidence_first_skips_data_answer_lead_for_template_structure_exclusivity():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "dataAnswer": {
            "profileKey": "structure_exclusivity",
            "summary": {
                "answer": "**Não** — nenhuma MP exclusiva; as **3** matérias-primas são compartilhadas.",
                "meaning": "A estrutura tem **5** componentes.",
            },
        },
        "textPresentation": {
            "markdown": (
                "### Estrutura com exclusividade — 90260882\n\n"
                "<!-- section:scope -->\n\n"
                "**Resposta:** Não — nenhuma MP exclusiva; as **3** matérias-primas são compartilhadas.\n"
                "BOM vigente do produto **90260882** (PROTETOR).\n"
                "Composição: **5** componente(s) · **2** PI · **3** MP"
            ),
        },
    }

    ChatRichPresentationTextService.prepare_evidence_first_chat_narrative(metadata)
    markdown = metadata["textPresentation"]["markdown"]

    assert markdown.lower().count("nenhuma mp exclusiva") == 1
    assert "A estrutura tem **5** componentes" not in markdown


def test_strip_highlights_block_removes_destaques_section():
    markdown = (
        "### Status fabril\n\n"
        "Produção: PA **Sim**.\n\n"
        "**Destaques**\n\n"
        "- Situação fabril consolidada.\n"
        "- Produção em andamento."
    )

    stripped = ChatRichPresentationTextService.strip_highlights_block(markdown)

    assert "**Destaques**" not in stripped
    assert "Produção em andamento." not in stripped
    assert "Produção: PA **Sim**." in stripped
