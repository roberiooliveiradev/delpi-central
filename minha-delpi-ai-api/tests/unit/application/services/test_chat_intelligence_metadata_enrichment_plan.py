from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)


def test_intelligence_metadata_includes_enrichment_plan_and_evidence_refs():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[],
        tool_context={
            "toolCalls": [],
            "enrichmentPlan": {
                "kind": "product_enrichment_composition",
                "plannedScopes": ["productSummary", "productStock", "productSales"],
                "executedCount": 3,
                "skippedByCap": 0,
            },
            "evidenceRefs": [
                {"path": "/products/90260148/stock", "operationId": "get_product_stock", "ok": True},
            ],
        },
    )

    assert metadata["enrichmentPlan"]["kind"] == "product_enrichment_composition"
    assert metadata["evidenceRefs"][0]["operationId"] == "get_product_stock"
