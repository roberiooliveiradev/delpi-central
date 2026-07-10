from app.application.services.chat_drawing_turn_enrichment_service import (
    ChatDrawingTurnEnrichmentService,
)
from app.domain.services.chat_drawing_analyser_presentation_suppression_service import (
    ChatDrawingAnalyserPresentationSuppressionService,
)


def _analyser_tool_call(**metadata):
    return {
        "name": "execute_external_action",
        "metadata": {
            "ok": True,
            "path": "/products/90260140/analyser",
            **metadata,
        },
    }


def test_suppression_strips_dashboard_and_render_plan_from_analyser():
    tool_context = {
        "drawingAnalysisMode": True,
        "drawingAnalysisExport": {"markdown": "## Relatório DELPI"},
        "toolCalls": [
            _analyser_tool_call(
                dashboardPresentation={
                    "type": "dashboard",
                    "title": "Painel consolidado",
                    "panels": [],
                },
                renderPlan={"segments": [{"kind": "dashboard", "slot": "primary"}]},
                treePresentation={"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
            )
        ],
    }

    result = ChatDrawingAnalyserPresentationSuppressionService.apply(tool_context)
    meta = result["toolCalls"][0]["metadata"]

    assert meta.get("dashboardPresentation") is None
    assert meta.get("renderPlan") is None
    assert meta.get("treePresentation") is None
    assert meta.get("suppressClientPresentation") is True
    assert meta.get("path") == "/products/90260140/analyser"


def test_suppression_skips_non_analyser_tool_calls():
    tool_context = {
        "drawingAnalysisExport": {"markdown": "## Relatório"},
        "toolCalls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/90260140/stock",
                    "dashboardPresentation": {"type": "dashboard", "panels": []},
                },
            }
        ],
    }

    result = ChatDrawingAnalyserPresentationSuppressionService.apply(tool_context)
    meta = result["toolCalls"][0]["metadata"]

    assert meta.get("dashboardPresentation") is not None
    assert meta.get("suppressClientPresentation") is not True


def test_suppression_skips_without_report_markdown():
    tool_context = {
        "toolCalls": [
            _analyser_tool_call(
                dashboardPresentation={"type": "dashboard", "title": "Painel", "panels": []},
            )
        ],
    }

    result = ChatDrawingAnalyserPresentationSuppressionService.apply(tool_context)
    meta = result["toolCalls"][0]["metadata"]

    assert meta.get("dashboardPresentation") is not None


def test_enrich_tool_context_suppresses_when_report_already_present():
    tool_context = {
        "drawingAnalysisMode": True,
        "drawingAnalysisExport": {"markdown": "## Relatório"},
        "toolCalls": [
            _analyser_tool_call(
                dashboardPresentation={"type": "dashboard", "title": "Painel consolidado", "panels": []},
            )
        ],
    }

    result = ChatDrawingTurnEnrichmentService.enrich_tool_context(
        tool_context,
        message="analise o desenho 90260140",
        attachment_ids=["att-1"],
    )
    meta = result["toolCalls"][0]["metadata"]

    assert meta.get("dashboardPresentation") is None
    assert meta.get("suppressClientPresentation") is True
