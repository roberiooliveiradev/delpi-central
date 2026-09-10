"""Orchestrator + shadow composer tests."""

from __future__ import annotations

from app.application.services.presentation_spec_composer_application_service import (
    PresentationSpecComposerApplicationService,
)
from app.domain.services.presentation_intelligence_orchestrator_service import (
    PresentationIntelligenceOrchestratorService,
)


def _heatmap_metadata():
    rows = []
    for product in ("P1", "P2"):
        for warehouse in ("W1", "W2"):
            rows.append(
                {
                    "product_code": product,
                    "warehouse": warehouse,
                    "unit": "UN",
                    "planned_qty": 5 if product == "P1" else 20,
                }
            )
    return {
        "path": "/external/plants",
        "userMessage": "mapa de calor produto × depósito com qtd planejada em tons de azul",
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "title": "Mapa",
            "data": rows,
            "config": {},
        },
        "presentationDecision": {"selected": "chart", "layoutMode": "single"},
    }


from app.domain.services.presentation_column_label_discovery_service import (
    PresentationColumnLabelDiscoveryService,
)


def test_orchestrator_compiles_heatmap_and_humanized_labels(monkeypatch):
    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: {}),
    )
    metadata = _heatmap_metadata()
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )
    assert summary.get("skipped") is not True
    chart = metadata["chartPresentation"]
    assert summary.get("specApplied") is True, summary
    assert chart["chartType"] == "heatmap"
    assert chart["config"]["xAxis"] in {"product_code", "warehouse"}
    assert chart["config"]["yAxis"] in {"product_code", "warehouse"}
    assert chart["config"]["yAxis"] != "unit"
    assert chart["config"]["valueKey"] == "planned_qty"
    labels = chart["config"]["fieldLabels"]
    assert labels["planned_qty"]
    assert labels["planned_qty"] != "planned_qty"
    assert " " in labels["planned_qty"] or labels["planned_qty"][0].isupper()


def test_orchestrator_preserves_existing_llm_column_labels(monkeypatch):
    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: {"mandatory_cc_pc": "NÃO USAR"}),
    )
    metadata = {
        "path": "/products/10080011/summary",
        "presentation": {
            "type": "table",
            "title": "Cadastro",
            "columns": [
                {"key": "mandatory_cc_pc", "label": "CC obrigatório PC"},
            ],
            "rows": [{"mandatory_cc_pc": "S", "sale_price": 1.2}],
        },
    }
    PresentationIntelligenceOrchestratorService.apply_before_render_plan(metadata)
    columns = {
        column["key"]: column["label"]
        for column in metadata["presentation"]["columns"]
        if isinstance(column, dict)
    }
    assert columns["mandatory_cc_pc"] == "CC obrigatório PC"
    bundle = metadata.get("resolvedFieldLabels") or {}
    assert (bundle.get("labels") or {}).get("mandatory_cc_pc") == "CC obrigatório PC"


def test_shadow_composer_validates_closed_candidate_set():
    class FakeLlm:
        def generate(self, messages):
            return """
            {
              "version": 1,
              "view": "chart",
              "mark": "heatmap",
              "encoding": {
                "x": {"field": "invented_field"},
                "y": {"field": "warehouse"},
                "color": {"field": "planned_qty"}
              }
            }
            """

        def stream(self, messages):
            yield ""

        def supports_structured_output(self):
            return False

    service = PresentationSpecComposerApplicationService(llm=FakeLlm())
    profile = {
        "fields": [
            {
                "key": "warehouse",
                "semanticType": "nominal",
                "cardinalityBand": "low",
                "isDimensionCandidate": True,
                "isMeasureCandidate": False,
            },
            {
                "key": "product_code",
                "semanticType": "identifier",
                "cardinalityBand": "low",
                "isDimensionCandidate": True,
                "isMeasureCandidate": False,
            },
            {
                "key": "planned_qty",
                "semanticType": "quantitative",
                "cardinalityBand": "medium",
                "isDimensionCandidate": False,
                "isMeasureCandidate": True,
            },
        ],
        "dimensionCandidates": ["warehouse", "product_code"],
        "measureCandidates": ["planned_qty"],
    }
    result = service.compose(intent={"mark": "heatmap"}, profile=profile)
    assert result["ok"] is False
    assert result["reason"] == "validation_failed"


def test_composer_repair_attempt_once_on_invalid_json():
    class FakeLlm:
        def __init__(self) -> None:
            self.calls = 0

        def generate(self, messages):
            self.calls += 1
            if self.calls == 1:
                return "not-json"
            return """
            {
              "version": 1,
              "view": "chart",
              "mark": "bar",
              "encoding": {
                "x": {"field": "warehouse"},
                "y": {"field": "planned_qty"}
              }
            }
            """

        def stream(self, messages):
            yield ""

        def supports_structured_output(self):
            return False

    llm = FakeLlm()
    service = PresentationSpecComposerApplicationService(llm=llm)
    profile = {
        "fields": [
            {
                "key": "warehouse",
                "semanticType": "nominal",
                "isDimensionCandidate": True,
                "isMeasureCandidate": False,
            },
            {
                "key": "planned_qty",
                "semanticType": "quantitative",
                "isDimensionCandidate": False,
                "isMeasureCandidate": True,
            },
        ],
        "dimensionCandidates": ["warehouse"],
        "measureCandidates": ["planned_qty"],
    }
    result = service.compose(intent={"mark": "bar"}, profile=profile)
    assert llm.calls == 2
    assert result["repairUsed"] is True
    assert result["ok"] is True


def test_ablation_c_beats_raw_first_numeric_for_produced_qty():
    from app.domain.services.presentation_data_profile_builder_service import (
        PresentationDataProfileBuilderService,
    )
    from app.domain.services.presentation_deterministic_intent_binder_service import (
        PresentationDeterministicIntentBinderService,
    )
    from app.domain.entities.presentation_spec import PresentationIntent

    rows = [
        {"machine": "M1", "planned_qty": 10, "produced_qty": 8},
        {"machine": "M2", "planned_qty": 12, "produced_qty": 11},
    ]
    # A: first numeric
    first_numeric = "planned_qty"
    # C: intent binder
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
    intent = PresentationIntent(
        view="chart",
        mark="bar",
        dimension_concepts=("máquina",),
        measure_concept="produzido",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    bound = spec.encoding["y"].field
    assert bound == "produced_qty"
    assert bound != first_numeric


def test_policy_gate_skips_when_spec_already_applied():
    assert (
        PresentationIntelligenceOrchestratorService.should_invoke_composer(
            {"specApplied": True, "bindConfidence": 0.9, "needsComposer": True},
            intent={"mark": "heatmap"},
        )
        is False
    )


def test_policy_gate_invokes_when_needs_composer():
    assert (
        PresentationIntelligenceOrchestratorService.should_invoke_composer(
            {"specApplied": False, "bindConfidence": 0.3, "needsComposer": True},
            intent={"view": "auto"},
            profile={
                "dimensionCandidates": ["a", "b"],
                "measureCandidates": ["m1", "m2"],
            },
        )
        is True
    )


def test_canary_authoritative_only_when_validation_ok(monkeypatch):
    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: {}),
    )
    metadata = _heatmap_metadata()
    PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )

    class GoodLlm:
        def generate(self, messages):
            return """
            {
              "version": 1,
              "view": "chart",
              "mark": "bar",
              "paletteFamily": "sequential-blue",
              "encoding": {
                "x": {"field": "warehouse"},
                "y": {"field": "planned_qty"}
              }
            }
            """

        def stream(self, messages):
            yield ""

        def supports_structured_output(self):
            return False

    monkeypatch.setenv("PRESENTATION_COMPOSER_CANARY", "1")
    monkeypatch.setenv("PRESENTATION_COMPOSER_SHADOW", "1")
    metadata["presentationIntelligence"]["needsComposer"] = True
    metadata["presentationIntelligence"]["specApplied"] = False
    metadata["presentationIntelligence"]["bindConfidence"] = 0.2
    metadata["presentationDataProfile"] = metadata.get("presentationDataProfile") or {
        "fields": [
            {"key": "product_code", "semanticType": "nominal", "isDimensionCandidate": True},
            {"key": "warehouse", "semanticType": "nominal", "isDimensionCandidate": True},
            {"key": "planned_qty", "semanticType": "quantitative", "isMeasureCandidate": True},
        ],
        "dimensionCandidates": ["product_code", "warehouse"],
        "measureCandidates": ["planned_qty"],
    }
    metadata["presentationIntent"] = metadata.get("presentationIntent") or {"mark": "bar"}

    service = PresentationSpecComposerApplicationService(llm=GoodLlm())
    service.apply_shadow_or_canary(metadata)

    assert metadata["presentationComposerShadow"]["ok"] is True
    assert metadata["presentationComposerShadow"]["specSummary"]["mark"] == "bar"
    assert metadata["presentationComposerPolicy"]["fallback"] is False
    assert metadata.get("presentationComposerAuthoritative") is True
    assert metadata.get("presentationComposerSpec") is not None


def test_canary_fallback_keeps_deterministic_when_composer_fails(monkeypatch):
    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, *args, **kwargs: {}),
    )
    metadata = _heatmap_metadata()
    PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=metadata["userMessage"],
    )
    chart_before = dict(metadata["chartPresentation"])

    class BadLlm:
        def generate(self, messages):
            return '{"version":1,"view":"chart","mark":"heatmap","encoding":{"x":{"field":"nope"}}}'

        def stream(self, messages):
            yield ""

        def supports_structured_output(self):
            return False

    monkeypatch.setenv("PRESENTATION_COMPOSER_CANARY", "1")
    monkeypatch.setenv("PRESENTATION_COMPOSER_SHADOW", "1")
    # Force invoke even if deterministic already applied.
    metadata["presentationIntelligence"]["needsComposer"] = True
    metadata["presentationIntelligence"]["specApplied"] = False
    metadata["presentationIntelligence"]["bindConfidence"] = 0.2
    metadata["presentationDataProfile"] = metadata.get("presentationDataProfile") or {
        "fields": [
            {"key": "product_code", "semanticType": "nominal", "isDimensionCandidate": True},
            {"key": "warehouse", "semanticType": "nominal", "isDimensionCandidate": True},
            {"key": "planned_qty", "semanticType": "quantitative", "isMeasureCandidate": True},
        ],
        "dimensionCandidates": ["product_code", "warehouse"],
        "measureCandidates": ["planned_qty"],
    }
    metadata["presentationIntent"] = metadata.get("presentationIntent") or {"mark": "heatmap"}

    service = PresentationSpecComposerApplicationService(llm=BadLlm())
    service.apply_shadow_or_canary(metadata)
    assert metadata["presentationComposerPolicy"]["fallback"] is True
    assert metadata.get("presentationComposerAuthoritative") is not True
    assert metadata["chartPresentation"]["chartType"] == chart_before["chartType"]
