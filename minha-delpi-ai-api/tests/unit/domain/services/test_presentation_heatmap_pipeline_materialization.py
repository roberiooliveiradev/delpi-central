"""PI pipeline — heatmap materialization (orchestrator → compiler slot)."""

from __future__ import annotations

from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)
from app.domain.services.presentation_intelligence_orchestrator_service import (
    PresentationIntelligenceOrchestratorService,
)

_ROWS = [
    {"product_code": "P1", "branch": "01", "warehouse": "01", "current_quantity": 10.0},
    {"product_code": "P1", "branch": "01", "warehouse": "50", "current_quantity": 0.0},
    {"product_code": "P1", "branch": "02", "warehouse": "01", "current_quantity": 20.0},
    {"product_code": "P1", "branch": "02", "warehouse": "99", "current_quantity": 5.0},
]

_MESSAGE = (
    "Agora coloque isso em um gráfico de mapa de calor "
    "(produto × depósito/filial) em tons de azul."
)


def test_orchestrator_materializes_heatmap_chart_slot_and_decision():
    metadata = {
        "path": "/products/P1/stock",
        "userMessage": _MESSAGE,
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": key} for key in _ROWS[0]],
            "rows": list(_ROWS),
        },
        "presentationDecision": {},
    }
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=_MESSAGE,
    )
    assert summary.get("specApplied") is True
    assert not summary.get("unmetIntent")
    chart = metadata.get("chartPresentation") or metadata.get("presentation")
    assert isinstance(chart, dict)
    assert chart.get("type") == "chart"
    assert chart.get("chartType") == "heatmap"
    config = chart.get("config") or {}
    assert config.get("xAxis") in {"branch", "warehouse"}
    assert config.get("yAxis") in {"branch", "warehouse"}
    assert config.get("xAxis") != config.get("yAxis")
    assert config.get("valueKey") == "current_quantity"
    assert config.get("paletteFamily") == "sequential-blue"
    decision = metadata.get("presentationDecision") or {}
    assert str(decision.get("selected") or "").lower() in {"heatmap", "chart"}
    ChatPresentationRenderPlanService.build(metadata)
    assert isinstance(metadata.get("renderPlan"), dict)


def test_negative_orchestrator_unmet_with_single_dimension():
    rows = [{"region": "N", "qty": 1.0}, {"region": "S", "qty": 2.0}]
    message = "mapa de calor região × região"
    metadata = {
        "userMessage": message,
        "tablePresentation": {
            "type": "table",
            "columns": [{"key": "region"}, {"key": "qty"}],
            "rows": rows,
        },
        "presentationDecision": {},
    }
    summary = PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=message,
    )
    chart = metadata.get("chartPresentation") or {}
    if isinstance(chart, dict) and chart.get("chartType") == "heatmap":
        # Same field twice should not materialize a valid matrix.
        assert summary.get("unmetIntent") or chart.get("chartType") != "heatmap"
    else:
        assert summary.get("unmetIntent") == "heatmap_not_materializable" or not summary.get(
            "specApplied"
        )
