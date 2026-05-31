from app.application.services.assistant_capabilities_catalog_generator import (
    AssistantCapabilitiesCatalogGenerator,
)


def test_generate_links_stock_action():
    catalog = AssistantCapabilitiesCatalogGenerator.generate(
        actions=[
            {
                "path": "/api/v1/stock/items",
                "enabled": True,
            }
        ],
        skills=[{"key": "company-knowledge"}],
        base_catalog={
            "version": "test",
            "features": [
                {
                    "id": "stock_lookup",
                    "title": "Estoque",
                    "category": "operational",
                    "status": "available",
                    "summary": "Saldo",
                    "requiresAgent": True,
                },
                {
                    "id": "rag",
                    "title": "RAG",
                    "category": "knowledge",
                    "status": "available",
                    "summary": "Docs",
                    "requiresAgent": False,
                },
            ],
        },
    )

    stock = next(item for item in catalog["features"] if item["id"] == "stock_lookup")
    rag = next(item for item in catalog["features"] if item["id"] == "rag")

    assert "/stock" in (stock.get("requiredActions") or [])
    assert rag.get("linkedSkills") == ["company-knowledge"]
    assert catalog.get("generation", {}).get("actionCount") == 1


def test_drift_report_detects_required_actions_change():
    on_disk = {
        "generation": {"generatedAt": "old"},
        "features": [{"id": "stock_lookup", "requiredActions": ["/stock"]}],
    }
    generated = {
        "generation": {"generatedAt": "new"},
        "features": [
            {"id": "stock_lookup", "requiredActions": ["/stock", "/products"]},
        ],
    }

    drift = AssistantCapabilitiesCatalogGenerator.drift_report(
        on_disk=on_disk,
        generated=generated,
    )

    assert drift
