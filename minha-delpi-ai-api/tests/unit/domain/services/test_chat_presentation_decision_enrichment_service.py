from app.domain.services.chat_presentation_decision_enrichment_service import (
    ChatPresentationDecisionEnrichmentService,
)


def test_enrich_attaches_presentation_decision():
    metadata = {
        "path": "/products/90269001/stock",
        "apiDelpiResponseMeta": {"entity": "product_stock"},
        "tablePresentation": {
            "type": "table",
            "rows": [{"filial": "01", "saldo": 10}],
        },
        "availableFormats": ["table", "text"],
    }

    result = ChatPresentationDecisionEnrichmentService.enrich(
        metadata,
        user_message="estoque do produto",
    )

    assert result.get("presentationDecision")
    assert result["presentationDecision"].get("selected") in {"table", "text", "kpi"}
