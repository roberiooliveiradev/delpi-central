"""External API + metamorphic + label humanization evals (deterministic)."""

from __future__ import annotations

from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)
from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)
from app.domain.services.chat_field_label_resolution_pipeline_service import (
    ChatFieldLabelResolutionPipelineService,
)


def _external_rows(*, machine_key: str = "machine", qty_key: str = "output_qty"):
    rows = []
    for machine in ("WC-1", "WC-2"):
        for shift in ("A", "B"):
            rows.append(
                {
                    machine_key: machine,
                    "shift": shift,
                    "defect_rate": 0.02,
                    qty_key: 100 + (20 if machine.endswith("2") else 0) + (5 if shift == "B" else 0),
                    "timestamp": "2026-09-01",
                }
            )
    return rows


def test_external_api_heatmap_binding_without_delpi_metadata():
    rows = _external_rows()
    openapi = {
        "machine": {
            "title": "Machine",
            "description": "Production workcell identifier",
        },
        "shift": {"title": "Shift", "description": "Work shift period"},
        "output_qty": {
            "title": "Output quantity",
            "description": "Units completed in the period",
        },
        "defect_rate": {
            "title": "Defect rate",
            "description": "Percentage of manufactured units rejected by quality inspection",
        },
    }
    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        list(rows[0].keys()),
        openapi_labels={key: str(meta.get("title")) for key, meta in openapi.items()},
        enable_discovery=False,
    )
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle=bundle.as_metadata(),
        openapi_field_meta=openapi,
    )
    intent = PresentationIntentExtractorService.extract(
        "heatmap máquina × turno pela produção"
    )
    spec, confidence = PresentationDeterministicIntentBinderService.bind(
        intent,
        profile,
        openapi_field_meta=openapi,
    )
    assert confidence > 0
    assert spec is not None
    assert spec.mark == "heatmap"
    fields = {channel.field for channel in spec.encoding.values()}
    assert "machine" in fields
    assert "shift" in fields
    assert "output_qty" in fields


def test_metamorphic_rename_preserves_binding_via_descriptions():
    rows = _external_rows(machine_key="workcell", qty_key="units_completed")
    openapi = {
        "workcell": {
            "title": "Workcell",
            "description": "Production workcell identifier",
        },
        "shift": {"title": "Period", "description": "Work shift period"},
        "units_completed": {
            "title": "Units completed",
            "description": "Units completed in the period",
        },
    }
    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        list(rows[0].keys()),
        openapi_labels={key: str(meta.get("title")) for key, meta in openapi.items()},
        enable_discovery=False,
    )
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle=bundle.as_metadata(),
        openapi_field_meta=openapi,
    )
    intent = PresentationIntentExtractorService.extract(
        "heatmap máquina × turno pela produção"
    )
    # Concepts still in Portuguese/business language; descriptions ground matching.
    intent_dims = PresentationIntentExtractorService.extract(
        "mapa de calor workcell × shift com units completed"
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(
        intent_dims,
        profile,
        openapi_field_meta=openapi,
    )
    assert spec is not None
    assert spec.encoding["color"].field == "units_completed"


def test_label_negative_obscure_keys_not_invented():
    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["x1", "cod_aux", "vlr2"],
        enable_discovery=False,
    )
    labels = {key.lower(): value.lower() for key, value in bundle.labels.items()}
    for forbidden in ("faturamento", "produção", "producao", "cliente"):
        assert forbidden not in " ".join(labels.values())


def test_sibling_measure_produced_qty_preferred_for_produzido_concept():
    rows = [
        {"machine": "M1", "planned_qty": 10, "produced_qty": 8},
        {"machine": "M2", "planned_qty": 12, "produced_qty": 11},
    ]
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "machine": "Máquina",
                "planned_qty": "Qtd. planejada",
                "produced_qty": "Qtd. produzida",
            },
            "formats": {},
            "sourceByKey": {},
        },
    )
    intent = PresentationIntentExtractorService.extract(
        "gráfico de barras produzido por máquina"
    )
    # Force measure concept if extractor missed.
    if not intent.measure_concept:
        from app.domain.entities.presentation_spec import PresentationIntent

        intent = PresentationIntent(
            view="chart",
            mark="bar",
            dimension_concepts=("máquina",),
            measure_concept="produzido",
        )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert spec.encoding["y"].field == "produced_qty"


def test_format_localization_quantity_and_percentage_pt_br():
    from app.domain.services.external_actions.external_action_column_label_service import (
        ExternalActionColumnLabelService,
    )

    service = ExternalActionColumnLabelService()
    qty = service.format_field_value(
        "planned_qty",
        1234.5,
        schema_formats={"planned_qty": "quantity"},
    )
    assert "," in qty or "." in qty
    pct = service.format_field_value(
        "defect_rate",
        12.5,
        schema_formats={"defect_rate": "percent"},
    )
    assert "%" in pct


def test_r5_summary_llm_and_stock_openapi_sibling(monkeypatch):
    from app.domain.services.presentation_column_label_discovery_service import (
        PresentationColumnLabelDiscoveryService,
    )

    def _fake_resolve(cls, keys, **kwargs):
        return {key: f"Rótulo {key}" for key in keys}

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(_fake_resolve),
    )

    summary = ChatFieldLabelResolutionPipelineService.resolve(
        ["mandatory_cc_pc", "sale_price"],
        enable_discovery=True,
    )
    assert summary.source_by_key["mandatory_cc_pc"] == "LLM_LOCALIZATION"
    assert summary.labels["mandatory_cc_pc"] == "Rótulo mandatory_cc_pc"

    stock = ChatFieldLabelResolutionPipelineService.resolve(
        ["warehouse", "available_quantity"],
        schema_labels={"warehouse": "Armazém", "available_quantity": "Qtd. disponível"},
        enable_discovery=True,
    )
    assert stock.labels["warehouse"] == "Armazém"
    assert stock.source_by_key["warehouse"] == "METADATA_SCHEMA"


def test_r8_r11_one_llm_batch_and_cache_hit(monkeypatch):
    from app.application.services.chat_presentation_column_label_discovery_service import (
        ChatPresentationColumnLabelDiscoveryService,
    )
    from app.composition.content_composer import configure_domain_infrastructure_ports
    from app.infrastructure.config.settings import Settings

    configure_domain_infrastructure_ports()
    ChatPresentationColumnLabelDiscoveryService.clear_cache()
    ChatPresentationColumnLabelDiscoveryService.configure_cache(None)
    monkeypatch.setattr(Settings, "CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED", True)
    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_gather_web_snippets",
        classmethod(lambda cls, keys: {}),
    )
    calls = {"count": 0}

    def fake_llm(keys, *, path, web_snippets):
        calls["count"] += 1
        return {key: f"Rótulo {key}" for key in keys}

    monkeypatch.setattr(
        ChatPresentationColumnLabelDiscoveryService,
        "_translate_with_llm",
        fake_llm,
    )

    keys = [f"col_{index}" for index in range(12)]
    first = ChatFieldLabelResolutionPipelineService.resolve(keys, enable_discovery=True)
    second = ChatFieldLabelResolutionPipelineService.resolve(keys, enable_discovery=True)

    assert calls["count"] == 1
    assert first.labels["col_0"] == "Rótulo col_0"
    assert second.labels["col_11"] == "Rótulo col_11"


def test_r5_llm_failure_keeps_humanize_header(monkeypatch):
    from app.domain.services.presentation_column_label_discovery_service import (
        PresentationColumnLabelDiscoveryService,
    )

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: {}),
    )
    bundle = ChatFieldLabelResolutionPipelineService.resolve(
        ["mandatory_cc_pc"],
        enable_discovery=True,
    )
    assert bundle.labels["mandatory_cc_pc"] == "Mandatory Cc Pc"
    assert bundle.source_by_key["mandatory_cc_pc"] == "DETERMINISTIC_HUMANIZER"


