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


def test_generate_maps_commercial_and_suppliers():
    catalog = AssistantCapabilitiesCatalogGenerator.generate(
        actions=[
            {"path": "/commercial/rol/series", "enabled": True},
            {"path": "/products/100/suppliers", "enabled": True},
            {"path": "/health", "enabled": True},
        ],
        skills=[],
        base_catalog={
            "version": "test",
            "features": [
                {
                    "id": "commercial_indicators",
                    "title": "Comercial",
                    "category": "indicators",
                    "status": "available",
                    "summary": "KPIs",
                    "requiresAgent": True,
                },
                {
                    "id": "product_lookup",
                    "title": "Produto",
                    "category": "operational",
                    "status": "available",
                    "summary": "Ficha",
                    "requiresAgent": True,
                },
            ],
        },
    )

    commercial = next(
        item for item in catalog["features"] if item["id"] == "commercial_indicators"
    )
    product = next(item for item in catalog["features"] if item["id"] == "product_lookup")
    generation = catalog.get("generation") or {}

    assert "/commercial" in (commercial.get("requiredActions") or [])
    assert "/suppliers" in (product.get("requiredActions") or [])
    assert "/health" not in (generation.get("unmappedActionPaths") or [])


def test_generate_maps_system_tables():
    catalog = AssistantCapabilitiesCatalogGenerator.generate(
        actions=[
            {"path": "/system/tables/{tableName}/schema", "enabled": True},
            {"path": "/system/login", "enabled": True},
        ],
        skills=[],
        base_catalog={
            "version": "test",
            "features": [
                {
                    "id": "system_metadata",
                    "title": "System",
                    "category": "operational",
                    "status": "available",
                    "summary": "SX2",
                    "requiresAgent": True,
                },
            ],
        },
    )

    system = catalog["features"][0]
    generation = catalog.get("generation") or {}

    assert "/system" in (system.get("requiredActions") or [])
    assert not generation.get("unmappedActionPaths")


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


def test_drift_report_ignores_action_count_only():
    features = [{"id": "stock_lookup", "requiredActions": ["/stock"]}]
    on_disk = {
        "generation": {"actionCount": 110, "enabledActionCount": 110, "pathRulesVersion": "2026.06.03"},
        "features": features,
    }
    generated = {
        "generation": {"actionCount": 0, "enabledActionCount": 0, "pathRulesVersion": "2026.06.03"},
        "features": features,
    }

    drift = AssistantCapabilitiesCatalogGenerator.drift_report(
        on_disk=on_disk,
        generated=generated,
    )

    assert not drift


def test_preserve_generation_counts_when_actions_missing():
    catalog = {
        "generation": {"actionCount": 0, "enabledActionCount": 0},
        "features": [],
    }
    previous = {
        "generation": {"actionCount": 42, "enabledActionCount": 40},
        "features": [],
    }

    AssistantCapabilitiesCatalogGenerator._preserve_generation_counts(
        catalog,
        previous=previous,
    )

    assert catalog["generation"]["actionCount"] == 42
    assert catalog["generation"]["enabledActionCount"] == 40
