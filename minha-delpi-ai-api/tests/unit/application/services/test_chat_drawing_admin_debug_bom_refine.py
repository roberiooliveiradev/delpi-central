from app.application.services.chat_drawing_admin_debug_service import (
    ChatDrawingAdminDebugService,
)


def test_build_trace_includes_bom_qty_refine_phase():
    trace = ChatDrawingAdminDebugService.build_trace(
        tool_context={
            "drawingAnalysisMode": True,
            "drawingPdfExtractSummary": {
                "productCode": "90263149",
                "legible": True,
                "bomVisionRefinement": {
                    "triggered": True,
                    "tableCount": 1,
                    "columnRowCount": 7,
                    "codesRefined": ["10090050"],
                },
            },
            "drawingAnalysis": {
                "productCode": "90263149",
                "status": "approved_with_notes",
                "criticalErrors": 0,
                "hasPdfAttachment": True,
                "visionRefinement": {
                    "attempted": True,
                    "resolved": 1,
                },
                "items": [],
            },
            "toolCalls": [],
        },
        intent_route={"intent": "drawing_analysis"},
        workspace_context={"skills": {"drawingAnalysis": True}},
    )

    assert trace is not None
    phase_ids = [phase["id"] for phase in trace["phases"]]
    assert "bom_qty_refine" in phase_ids

    refine_phase = next(phase for phase in trace["phases"] if phase["id"] == "bom_qty_refine")

    assert refine_phase["status"] == "ok"
    assert refine_phase["codesRefined"] == ["10090050"]
