from app.application.services.chat_drawing_follow_up_service import (
    ChatDrawingFollowUpService,
)
from app.application.services.chat_drawing_metrics_service import (
    ChatDrawingMetricsService,
)


def test_build_snapshot_counts_statuses():
    drawing = {
        "productCode": "90260140",
        "status": "rejected",
        "overallLabel": "Reprovado",
        "criticalErrors": 2,
        "errors": 1,
        "warnings": 0,
        "hasPdfAttachment": True,
        "pdfLegible": True,
        "items": [
            {"section": "BOM", "status": "critical_error"},
            {"section": "Roteiro", "status": "ok"},
            {"section": "Cabeçalho", "status": "critical_error"},
        ],
    }

    snapshot = ChatDrawingMetricsService.build_snapshot(
        drawing,
        latency_ms=1200,
        report_exported=True,
        analyser_ok=True,
    )

    assert snapshot["productCode"] == "90260140"
    assert snapshot["overallStatus"] == "rejected"
    assert snapshot["criticalErrors"] == 2
    assert snapshot["checklistItems"] == 3
    assert snapshot["itemsByStatus"]["critical_error"] == 2
    assert snapshot["reportExported"] is True
    assert snapshot["analyserOk"] is True
    assert snapshot["latencyMs"] == 1200


def test_attach_to_assistant_metadata():
    metadata: dict = {}
    tool_context = {
        "drawingAnalysis": {
            "productCode": "90260140",
            "status": "approved",
            "criticalErrors": 0,
            "items": [{"section": "API", "status": "ok"}],
        },
        "drawingAnalysisExport": {"markdown": "# Rel"},
        "toolCalls": [
            {
                "metadata": {"ok": True, "path": "/products/90260140/analyser"},
            }
        ],
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": tool_context["drawingAnalysis"]},
        tool_context=tool_context,
        latency_ms=500,
    )

    metrics = metadata.get("drawingAnalysisMetrics")

    assert isinstance(metrics, dict)
    assert metrics["productCode"] == "90260140"
    assert metrics["latencyMs"] == 500
    assert metrics["analyserOk"] is True


def test_enrich_audit_metadata():
    audit = {"session_id": "s1"}
    enriched = ChatDrawingMetricsService.enrich_audit_metadata(
        audit,
        tool_context={
            "drawingAnalysis": {
                "productCode": "90260140",
                "status": "incomplete",
                "items": [],
            }
        },
    )

    assert "drawingAnalysis" in enriched
    assert enriched["drawingAnalysis"]["overallStatus"] == "incomplete"
