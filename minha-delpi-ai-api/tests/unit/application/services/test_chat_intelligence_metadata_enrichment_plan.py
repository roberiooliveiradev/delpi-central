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


def test_intelligence_metadata_includes_sufficiency_after_follow_up():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[],
        tool_context={
            "toolCalls": [],
            "enrichmentPlan": {
                "kind": "product_enrichment_composition",
                "executedCount": 2,
                "anomalyFollowUps": ["productSales"],
                "sufficiency": {
                    "verdict": "execute",
                    "planId": "stock_low_needs_sales",
                    "executedRouteIds": ["productSales"],
                    "deferredToChips": False,
                    "reasonKey": "stockLowNeedsSales",
                },
            },
            "evidenceRefs": [
                {"path": "/products/x/stock", "operationId": "get_product_stock", "ok": True},
                {"path": "/products/x/sales", "operationId": "get_product_sales", "ok": True},
            ],
        },
    )

    assert metadata["enrichmentPlan"]["sufficiency"]["planId"] == "stock_low_needs_sales"
    assert metadata["enrichmentPlan"]["sufficiency"]["executedRouteIds"] == ["productSales"]
    assert len(metadata["evidenceRefs"]) == 2
