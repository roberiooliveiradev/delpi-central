from app.application.services.chat_presentation_column_label_discovery_service import (
    ChatPresentationColumnLabelDiscoveryService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
    invalidate_column_label_cache,
)
from app.domain.services.presentation_column_label_discovery_service import (
    PresentationColumnLabelDiscoveryService,
)
from app.infrastructure.config.settings import Settings


def test_discovery_service_skips_catalog_fields(monkeypatch):
    configure_domain_infrastructure_ports()
    ChatPresentationColumnLabelDiscoveryService.clear_cache()
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED", True)

    llm_called = {"count": 0}

    def fake_llm(keys, *, path, web_snippets):
        llm_called["count"] += 1
        return {"unknown_field_xyz": "Campo desconhecido"}

    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        fake_llm,
    )

    labels = ChatPresentationColumnLabelDiscoveryService.resolve_labels(
        ["unit", "unknown_field_xyz"],
        path="/products/1/cost-impact-simulation",
        fields={"unit": "Unidade"},
    )

    assert "unknown_field_xyz" in labels
    assert labels["unknown_field_xyz"] == "Campo desconhecido"
    assert "unit" not in labels
    assert llm_called["count"] == 1


def test_discovery_service_uses_cache(monkeypatch):
    configure_domain_infrastructure_ports()
    ChatPresentationColumnLabelDiscoveryService.clear_cache()
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED", True)

    calls = {"count": 0}

    def fake_llm(keys, *, path, web_snippets):
        calls["count"] += 1
        return {key: f"Rótulo {key}" for key in keys}

    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        fake_llm,
    )

    first = ChatPresentationColumnLabelDiscoveryService.resolve_labels(
        ["brand_new_field"],
        path="/test",
        fields={},
    )
    second = ChatPresentationColumnLabelDiscoveryService.resolve_labels(
        ["brand_new_field"],
        path="/test",
        fields={},
    )

    assert first["brand_new_field"] == "Rótulo brand_new_field"
    assert second["brand_new_field"] == "Rótulo brand_new_field"
    assert calls["count"] == 1


def test_resolve_columns_applies_discovered_labels(monkeypatch):
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED", True)

    def fake_resolve(keys, *, path="", schema_labels=None, profile_labels=None, fields=None):
        if "future_api_field" in keys:
            return {"future_api_field": "Campo futuro API"}
        return {}

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: fake_resolve(*args, **kwargs)),
    )

    service = ExternalActionColumnLabelService()
    columns = service.resolve_columns_for_items(
        [{"rank": 1, "future_api_field": "x", "unit": "MT"}],
        path="/products/90261255/cost-impact-simulation",
        profile_name="costImpactMaterials",
    )
    labels = {column["key"]: column["label"] for column in columns}

    assert labels["future_api_field"] == "Campo futuro API"
    assert labels["unit"] == "Unid."
