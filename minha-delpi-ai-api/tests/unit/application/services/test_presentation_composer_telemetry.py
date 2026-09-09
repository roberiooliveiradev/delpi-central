"""Telemetry fields for Presentation Composer shadow/canary."""

from __future__ import annotations

import json

from app.application.services.presentation_spec_composer_application_service import (
    PresentationSpecComposerApplicationService,
)


def _profile() -> dict:
    return {
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


def test_shadow_telemetry_has_policy_and_summary_without_rows_or_prompt(monkeypatch):
    class FakeLlm:
        def generate(self, messages):
            blob = json.dumps(messages, ensure_ascii=False)
            assert "rows" not in blob.lower()
            assert "sampleRows" not in blob
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

    monkeypatch.setenv("PRESENTATION_COMPOSER_SHADOW", "1")
    metadata = {
        "userMessage": "mapa de calor azul",
        "presentationIntelligence": {
            "specApplied": False,
            "bindConfidence": 0.2,
            "needsComposer": True,
        },
        "presentationIntent": {"mark": "bar"},
        "presentationDataProfile": _profile(),
    }

    PresentationSpecComposerApplicationService(llm=FakeLlm()).apply_shadow_or_canary(metadata)

    policy = metadata["presentationComposerPolicy"]
    shadow = metadata["presentationComposerShadow"]
    assert policy["decision"] == "invoke"
    assert policy["shadowEnabled"] is True
    assert policy["canaryEnabled"] is False
    assert isinstance(policy["latencyMs"], (int, float))
    assert policy["fallback"] is True
    assert shadow["ok"] is True
    assert shadow["specSummary"]["mark"] == "bar"
    assert shadow["specSummary"]["paletteFamily"] == "sequential-blue"
    assert "spec" not in shadow
    assert "rows" not in json.dumps(shadow, ensure_ascii=False)
    assert "prompt" not in json.dumps(shadow, ensure_ascii=False).lower()
