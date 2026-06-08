from app.domain.services.chat_rich_presentation_canvas_export_service import (
    ChatRichPresentationCanvasExportService,
)


def _analyser_metadata():
    return {
        "toolCalls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "textPresentation": {
                        "markdown": (
                            "### Informações completas do produto 90260015\n\n"
                            "**Destaques**\n\n- Estrutura com 4 itens."
                        ),
                    },
                    "tablePresentations": [
                        {
                            "type": "table",
                            "title": "Produto 90260015",
                            "columns": [
                                {"key": "campo", "label": "Campo"},
                                {"key": "valor", "label": "Valor"},
                            ],
                            "rows": [
                                {"campo": "Código", "valor": "90260015"},
                                {"campo": "Bloqueio", "valor": "2"},
                            ],
                        },
                        {
                            "type": "table",
                            "title": "Roteiro de produção — 90260015",
                            "columns": [
                                {"key": "product_code", "label": "Produto"},
                                {"key": "operation_description", "label": "Operação"},
                            ],
                            "rows": [
                                {
                                    "product_code": "90260015",
                                    "operation_description": "EMBALAR",
                                }
                            ],
                        },
                    ],
                    "presentation": {
                        "type": "tree",
                        "title": "Estrutura do produto 90260015",
                        "root": {
                            "id": "90260015",
                            "label": "90260015",
                            "subtitle": "CHICOTE DE LIGACAO",
                            "badge": "PA",
                            "meta": {"quantity": 1, "unit": "MI"},
                            "children": [
                                {
                                    "id": "50210372",
                                    "label": "50210372",
                                    "badge": "PI",
                                    "meta": {"quantity": 1, "unit": "MI"},
                                    "children": [
                                        {
                                            "id": "10420040",
                                            "label": "10420040",
                                            "badge": "MP",
                                            "meta": {"quantity": 142, "unit": "MT"},
                                        }
                                    ],
                                }
                            ],
                        },
                    },
                    "chartPresentation": {
                        "type": "chart",
                        "title": "Composição por tipo de componente",
                        "chartType": "donut",
                        "data": [
                            {"label": "MP (7)", "value": 7},
                            {"label": "PI (2)", "value": 2},
                        ],
                    },
                },
            }
        ]
    }


def test_build_markdown_includes_tables_tree_and_chart():
    metadata = _analyser_metadata()
    content = metadata["toolCalls"][0]["metadata"]["textPresentation"]["markdown"]

    markdown = ChatRichPresentationCanvasExportService.build_markdown_from_assistant(
        content,
        metadata,
    )

    assert "90260015" in markdown
    assert "Produto 90260015" in markdown
    assert "Roteiro de produção" in markdown
    assert "Estrutura do produto 90260015" in markdown
    assert "10420040" in markdown
    assert "Composição por tipo de componente" in markdown
    assert "MP (7)" in markdown


def test_sections_from_tool_metadata_skips_text_presentation():
    metadata = _analyser_metadata()["toolCalls"][0]["metadata"]
    sections = ChatRichPresentationCanvasExportService.sections_from_tool_metadata(metadata)

    assert any("Produto 90260015" in section for section in sections)
    assert not any("**Destaques**" in section for section in sections)
