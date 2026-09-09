from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_field_label_resolution_pipeline_service import (
    ChatFieldLabelResolutionPipelineService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    invalidate_column_label_cache,
)
from app.domain.services.presentation_column_label_discovery_service import (
    PresentationColumnLabelDiscoveryService,
)


def test_field_label_bundle_meta_wins_over_catalog():
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()

    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["last_price", "unit_price"],
        schema_labels={"last_price": "Preço da meta"},
        enable_discovery=False,
    )

    assert bundle.labels["last_price"] == "Preço da meta"
    assert bundle.source_by_key["last_price"] == "METADATA_SCHEMA"
    assert bundle.labels["unit_price"] == "Preço unitário"
    assert bundle.source_by_key["unit_price"] == "CANONICAL_VOCABULARY"


def test_field_label_bundle_humanize_marked_without_discovery(monkeypatch):
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *a, **k: (_ for _ in ()).throw(AssertionError("no discovery"))),
    )

    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["totally_unknown_metric_xyz"],
        enable_discovery=False,
    )

    assert bundle.source_by_key["totally_unknown_metric_xyz"] == "DETERMINISTIC_HUMANIZER"
    assert "Unknown" in bundle.labels["totally_unknown_metric_xyz"] or "Metric" in bundle.labels[
        "totally_unknown_metric_xyz"
    ]


def test_field_label_bundle_discovery_only_for_pending(monkeypatch):
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()
    calls: list[list[str]] = []

    def _fake_resolve(cls, keys, **kwargs):
        calls.append(list(keys))
        return {key: f"Descoberto {key}" for key in keys}

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(_fake_resolve),
    )

    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["last_price", "weird_pending_field"],
        enable_discovery=True,
    )

    assert bundle.labels["last_price"] == "Últ. preço"
    assert bundle.source_by_key["last_price"] == "CANONICAL_VOCABULARY"
    assert calls and calls[0] == ["weird_pending_field"]
    assert bundle.labels["weird_pending_field"] == "Descoberto weird_pending_field"
    assert bundle.source_by_key["weird_pending_field"] == "LLM_LOCALIZATION"
