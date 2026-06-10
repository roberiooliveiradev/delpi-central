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
