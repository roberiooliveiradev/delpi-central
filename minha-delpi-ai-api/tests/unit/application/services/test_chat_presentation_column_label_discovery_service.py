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


def _disable_web_and_enable_discovery(monkeypatch):
    configure_domain_infrastructure_ports()
    ChatPresentationColumnLabelDiscoveryService.clear_cache()
    ChatPresentationColumnLabelDiscoveryService.configure_cache(None)
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED", True)
    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_gather_web_snippets",
        classmethod(lambda cls, keys: {}),
    )


def test_discovery_service_skips_openapi_schema_labels(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)

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
        schema_labels={"unit": "Unidade"},
    )

    assert "unknown_field_xyz" in labels
    assert labels["unknown_field_xyz"] == "Campo desconhecido"
    assert "unit" not in labels
    assert llm_called["count"] == 1


def test_discovery_service_uses_cache(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)

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
    _disable_web_and_enable_discovery(monkeypatch)
    invalidate_column_label_cache()

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
    assert labels["unit"] == "Unit"


def test_discovery_batches_more_than_eight_pending_keys(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_MAX_KEYS", 64)

    seen: list[list[str]] = []

    def fake_llm(keys, *, path, web_snippets):
        seen.append(list(keys))
        return {key: f"Rótulo {key}" for key in keys}

    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        fake_llm,
    )

    keys = [f"field_{index}" for index in range(12)]
    labels = ChatPresentationColumnLabelDiscoveryService.resolve_labels(keys, path="/products/1")

    assert seen and len(seen[0]) == 12
    assert labels["field_0"] == "Rótulo field_0"
    assert labels["field_11"] == "Rótulo field_11"

    bundle = ExternalActionColumnLabelService().resolve_field_label_bundle(
        ["mandatory_cc_pc"],
        enable_discovery=True,
    )
    assert bundle.labels["mandatory_cc_pc"] == "Rótulo mandatory_cc_pc"
    assert bundle.source_by_key["mandatory_cc_pc"] == "LLM_LOCALIZATION"


def test_empty_llm_falls_back_to_humanize(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)
    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        lambda keys, *, path, web_snippets: {},
    )

    bundle = ExternalActionColumnLabelService().resolve_field_label_bundle(
        ["mandatory_cc_pc"],
        enable_discovery=True,
    )
    assert bundle.labels["mandatory_cc_pc"] == "Mandatory Cc Pc"
    assert bundle.source_by_key["mandatory_cc_pc"] == "DETERMINISTIC_HUMANIZER"


def test_llm_english_humanize_equivalent_is_rejected(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)
    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        lambda keys, *, path, web_snippets: {"mandatory_cc_pc": "Mandatory Cc Pc"},
    )

    bundle = ExternalActionColumnLabelService().resolve_field_label_bundle(
        ["mandatory_cc_pc"],
        enable_discovery=True,
    )
    assert bundle.labels["mandatory_cc_pc"] == "Mandatory Cc Pc"
    assert bundle.source_by_key["mandatory_cc_pc"] == "DETERMINISTIC_HUMANIZER"


def test_persistent_cache_skips_second_llm(monkeypatch):
    _disable_web_and_enable_discovery(monkeypatch)
    store: dict[str, str] = {}

    class FakeCache:
        def get_label(self, field_key: str) -> str | None:
            return store.get(field_key)

        def put_label(self, field_key: str, label: str, *, source: str = "LLM_LOCALIZATION") -> None:
            store[field_key] = label

    ChatPresentationColumnLabelDiscoveryService.configure_cache(FakeCache())
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
        ["persisted_field_abc"],
        path="/test",
    )
    ChatPresentationColumnLabelDiscoveryService.clear_cache()
    second = ChatPresentationColumnLabelDiscoveryService.resolve_labels(
        ["persisted_field_abc"],
        path="/test",
    )

    assert first["persisted_field_abc"] == "Rótulo persisted_field_abc"
    assert second["persisted_field_abc"] == "Rótulo persisted_field_abc"
    assert calls["count"] == 1
    ChatPresentationColumnLabelDiscoveryService.configure_cache(None)
