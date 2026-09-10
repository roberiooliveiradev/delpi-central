"""H-CAP-04 — capability UX classification without path authority."""

from __future__ import annotations

from app.domain.services.capability_ux_classifier_service import (
    CapabilityUxClassifierService,
)
from app.domain.services.chat_capabilities_catalog_answer_service import (
    ChatCapabilitiesCatalogAnswerService,
)
from app.infrastructure.external_actions.openapi_action_importer import OpenApiActionImporter


def test_entity_shape_classifies_stock_without_path_token():
    action = {
        "summary": "Consultar disponibilidade",
        "description": "",
        "path": "/acme/widgets/{id}/availability",
        "tags": ["widgets"],
        "delpi_metadata": {"entity": "product", "shape": "stock"},
    }
    classified = CapabilityUxClassifierService.classify_action(action)
    assert classified["category"] == "Estoque de produto"
    assert classified["source"] == "entity_shape"


def test_keyword_classifies_without_x_delpi_or_known_path():
    action = {
        "summary": "List widget inventory by branch",
        "description": "Return warehouse inventory positions",
        "path": "/never-seen/vendor/v9/items/{sku}/on-hand",
        "tags": ["inventory"],
        "operation_id": "listWidgetOnHand",
    }
    classified = CapabilityUxClassifierService.classify_action(action)
    assert classified["category"] == "Estoque de produto"
    assert classified["source"] == "keyword"
    assert "path" not in str(classified.get("source") or "")


def test_metamorphic_rename_keeps_ux_family():
    base = {
        "summary": "Consultar estoque do produto por filial",
        "description": "Saldo disponível",
        "tags": ["products", "stock"],
    }
    a = CapabilityUxClassifierService.classify_action(
        {
            **base,
            "path": "/products/{code}/stock",
            "operation_id": "getProductStock",
            "provider_key": "api-delpi",
        }
    )
    b = CapabilityUxClassifierService.classify_action(
        {
            **base,
            "path": "/catalog/v2/items/{sku}/on-hand-balance",
            "operation_id": "fetchItemOnHandBalance",
            "provider_key": "acme-erp",
        }
    )
    assert a["category"] == b["category"] == "Estoque de produto"


def test_unknown_without_signals_falls_back_generic():
    classified = CapabilityUxClassifierService.classify_action(
        {
            "summary": "Ping probe",
            "description": "liveness",
            "path": "/z9/qq/___",
            "tags": ["z9"],
            "operation_id": "pingProbeZ9",
        }
    )
    assert classified["category"] == "Outras consultas"
    assert classified["confidence"] == "low"


def test_importer_persists_ux_capability_in_delpi_metadata():
    schema = {
        "paths": {
            "/widgets/{id}/inventory": {
                "get": {
                    "operationId": "getWidgetInventory",
                    "tags": ["Widgets"],
                    "summary": "List widget inventory",
                    "description": "Warehouse stock positions",
                }
            }
        }
    }
    actions = OpenApiActionImporter().import_actions("acme-widgets", schema)
    assert len(actions) == 1
    meta = actions[0].get("delpi_metadata") or {}
    ux = meta.get("uxCapability") or {}
    assert ux.get("category") == "Estoque de produto"


def test_format_action_catalog_uses_ux_capability_not_path_token():
    text_lines = ChatCapabilitiesCatalogAnswerService.format_action_catalog(
        [
            {
                "actionId": "acme.widgets.inventory",
                "method": "GET",
                "path": "/acme/v1/widgets/{id}/on-hand",
                "summary": "Consultar estoque do widget",
                "delpiMetadata": {
                    "uxCapability": {
                        "category": "Estoque de produto",
                        "examples": ["estoque do widget 1"],
                        "source": "test",
                        "confidence": "high",
                    }
                },
            }
        ],
        ["acme.widgets.inventory"],
    )
    blob = "\n".join(text_lines)
    assert "**Estoque de produto**" in blob
    assert "/acme/v1/widgets" in blob
