from app.domain.services.chat_presentation_humanized_narrative_service import (
    ChatPresentationHumanizedNarrativeService,
)


def test_enrich_metadata_adds_panorama_and_conclusion_for_thin_markdown():
    metadata = {
        "path": "/products/90269002/factory-status",
        "textPresentation": {
            "title": "Status fabril",
            "markdown": "### Status fabril\n\n<!-- section:scope -->\n\nResumo curto.",
        },
        "profileTablePresentation": {
            "type": "table",
            "role": "profile",
            "rows": [
                {"campo": "Produto", "valor": "90269002"},
                {"campo": "Situação", "valor": "Em produção"},
            ],
        },
        "kpiPresentation": {
            "type": "kpi",
            "cards": [
                {"label": "OPs abertas", "value": 3, "unit": ""},
            ],
        },
        "tablePresentations": [
            {
                "type": "table",
                "role": "list",
                "rows": [{"op": "001"}],
            }
        ],
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)
    markdown = metadata["textPresentation"]["markdown"]

    assert "**Panorama**" in markdown
    assert "**Leitura rápida**" in markdown
    assert "painéis abaixo" in markdown.lower()


def test_enrich_metadata_skips_pricing_route():
    metadata = {
        "path": "/products/10080001/pricing",
        "textPresentation": {
            "markdown": "### Preço\n\nTexto curto.",
        },
        "tablePresentations": [{"type": "table", "role": "profile", "rows": [{"campo": "x", "valor": "y"}]}],
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "Menor", "value": 1, "unit": "R$"}]},
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)

    assert "**Panorama**" not in metadata["textPresentation"]["markdown"]


def test_enrich_metadata_skips_stock_profile():
    metadata = {
        "path": "/products/10080001/stock",
        "apiDelpiResponseMeta": {"entity": "product_stock"},
        "textPresentation": {
            "markdown": "### Estoque\n\nTexto curto.",
        },
        "tablePresentations": [{"type": "table", "role": "profile", "rows": [{"campo": "x", "valor": "y"}]}],
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "Saldo", "value": 1, "unit": ""}]},
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)

    assert "**Panorama**" not in metadata["textPresentation"]["markdown"]


def test_enrich_metadata_skips_structure_exclusivity_profile():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
        "textPresentation": {
            "markdown": (
                "### Estrutura com exclusividade — 90260882\n\n"
                "**Resposta:** Não — nenhuma MP exclusiva."
            ),
        },
        "kpiPresentation": {
            "type": "kpi",
            "cards": [{"label": "MPs exclusivas", "value": 0, "unit": "MP"}],
        },
        "tablePresentations": [{"type": "table", "role": "profile", "rows": [{"campo": "x", "valor": "y"}]}],
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)

    assert "**Panorama**" not in metadata["textPresentation"]["markdown"]


def test_enrich_metadata_skips_conclusion_for_pagination_only_kpi():
    metadata = {
        "path": "/products/10080001/structure",
        "textPresentation": {
            "title": "Estrutura",
            "markdown": "### Estrutura\n\n<!-- section:scope -->\n\nNenhum componente.",
        },
        "kpiPresentation": {
            "type": "kpi",
            "cards": [
                {"label": "Total Pages", "value": 0, "unit": ""},
                {"label": "Page Size", "value": 50, "unit": ""},
            ],
        },
        "tablePresentations": [
            {
                "type": "table",
                "role": "list",
                "rows": [],
            }
        ],
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)
    markdown = metadata["textPresentation"]["markdown"]

    assert "Total Pages" not in markdown
    assert "painéis abaixo" not in markdown.lower()


def test_enrich_metadata_skips_panorama_for_structure_components_table():
    metadata = {
        "path": "/products/90260149/structure",
        "apiDelpiResponseMeta": {"entity": "product_structure"},
        "textPresentation": {
            "title": "Estrutura do produto 90260149",
            "markdown": (
                "### Estrutura do produto 90260149\n\n"
                "Produto **90260149**: CHICOTE.\n\n"
                "A composição possui **6** componente(s) de nível 1."
            ),
        },
        "profileTablePresentation": {
            "type": "table",
            "title": "Componentes da estrutura 90260149",
            "columns": [
                {"key": "parent_code", "label": "PI pai"},
                {"key": "component_code", "label": "Componente"},
            ],
            "rows": [
                {
                    "parent_code": "90260149",
                    "component_code": "C1",
                    "description": "COMP",
                    "quantity": 1.0,
                }
            ],
        },
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura do produto 90260149",
            "root": {"id": "90260149", "label": "90260149", "children": []},
        },
    }

    ChatPresentationHumanizedNarrativeService.enrich_metadata(metadata)
    markdown = metadata["textPresentation"]["markdown"]

    assert "**Panorama**" not in markdown
    assert "—:" not in markdown
