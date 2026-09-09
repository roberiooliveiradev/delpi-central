"""BUG_A_BASELINE — heatmap paren + partial bind (desired behavior; xfail until E1).

Fixtures genéricas (P1 / branch / warehouse / current_quantity) — sem códigos corporativos.
"""

from __future__ import annotations

import pytest

from app.domain.entities.presentation_spec import PresentationIntent
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)
from app.domain.services.presentation_intelligence_orchestrator_service import (
    PresentationIntelligenceOrchestratorService,
)
from app.domain.services.presentation_intent_extractor_service import (
    PresentationIntentExtractorService,
)

_BUG_A = pytest.mark.xfail(
    strict=True,
    reason="BUG_A_BASELINE: extractor paren noise + binder partial completion",
)

_STOCK_LIKE_ROWS = [
    {
        "product_code": "P1",
        "branch": "01",
        "warehouse": "01",
        "current_quantity": 10.0,
    },
    {
        "product_code": "P1",
        "branch": "01",
        "warehouse": "50",
        "current_quantity": 0.0,
    },
    {
        "product_code": "P1",
        "branch": "02",
        "warehouse": "01",
        "current_quantity": 20.0,
    },
    {
        "product_code": "P1",
        "branch": "02",
        "warehouse": "99",
        "current_quantity": 5.0,
    },
]

_P0_MESSAGE = (
    "Agora coloque isso em um gráfico de mapa de calor "
    "(produto × depósito/filial) em tons de azul."
)


def _stock_like_profile():
    return PresentationDataProfileBuilderService.build(_STOCK_LIKE_ROWS)


def test_bug_a_baseline_extractor_paren_axes_are_short():
    intent = PresentationIntentExtractorService.extract(_P0_MESSAGE)
    assert intent.mark == "heatmap"
    assert intent.palette_family == "sequential-blue"
    joined = " ".join(intent.dimension_concepts).lower()
    assert "agora coloque" not in joined
    assert any("produto" in concept for concept in intent.dimension_concepts)
    assert any(
        "depósito" in concept or "deposito" in concept or "filial" in concept
        for concept in intent.dimension_concepts
    )


@_BUG_A
def test_bug_a_baseline_binder_completes_partial_single_axis_match():
    """Um único concept discriminante não deve impedir completar o 2º eixo."""
    profile = _stock_like_profile()
    assert len(profile.dimension_candidates) >= 2
    intent = PresentationIntent(
        view="chart",
        mark="heatmap",
        dimension_concepts=("depósito",),
        palette_family="sequential-blue",
    )
    spec, _confidence = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert spec.mark == "heatmap"
    assert "x" in spec.encoding and "y" in spec.encoding and "color" in spec.encoding
    assert spec.encoding["x"].field != spec.encoding["y"].field
    assert spec.encoding["x"].field in profile.dimension_candidates
    assert spec.encoding["y"].field in profile.dimension_candidates
    assert "warehouse" in {
        spec.encoding["x"].field,
        spec.encoding["y"].field,
    }


@_BUG_A
def test_bug_a_baseline_orchestrator_materializes_heatmap():
    metadata = {
        "path": "/products/P1/stock",
        "userMessage": _P0_MESSAGE,
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key} for key in _STOCK_LIKE_ROWS[0]],
            "rows": list(_STOCK_LIKE_ROWS),
        },
        "presentationDecision": {},
    }
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=_P0_MESSAGE,
    )
    assert summary.get("unmetIntent") in (None, "")
    chart = metadata.get("chartPresentation") or metadata.get("presentation")
    assert isinstance(chart, dict)
    assert chart.get("chartType") == "heatmap"
