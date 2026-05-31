from app.application.services.chat_admin_debug_service import ChatAdminDebugService
from app.application.services.chat_drawing_admin_debug_service import (
    ChatDrawingAdminDebugService,
)


def test_build_trace_full_drawing_turn():
    trace = ChatDrawingAdminDebugService.build_trace(
        tool_context={
            "drawingAnalysisMode": True,
            "drawingPdfExtractSummary": {
                "productCode": "90260140",
                "revision": "01",
                "legible": True,
                "componentCount": 1,
            },
            "drawingAnalysis": {
                "productCode": "90260140",
                "status": "approved",
                "criticalErrors": 0,
                "hasPdfAttachment": True,
                "items": [{"section": "BOM", "item": "X", "status": "ok"}],
            },
            "drawingAnalysisExport": {"filename": "relatorio-desenho-90260140-20260531.md"},
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/90260140/analyser",
                        "statusCode": 200,
                        "actionId": "get_product_analyser",
                    },
                    "arguments": {"code": "90260140"},
                }
            ],
        },
        intent_route={"intent": "drawing_analysis", "confidence": 0.9},
        workspace_context={"skills": {"drawingAnalysis": True}},
    )

    assert trace is not None
    assert trace["active"] is True
    phase_ids = [phase["id"] for phase in trace["phases"]]
    assert phase_ids == ["intent", "skill", "pdf_extraction", "analyser", "validation", "report"]
    assert trace["phases"][2]["status"] == "ok"
    assert trace["phases"][3]["status"] == "ok"
    assert trace["summary"]["productCode"] == "90260140"


def test_admin_debug_payload_includes_drawing_trace():
    payload = ChatAdminDebugService.build(
        workspace_context={"skills": {"drawingAnalysis": True}},
        tool_context={
            "drawingAnalysisMode": True,
            "drawingAnalysis": {"productCode": "90260140", "items": [], "criticalErrors": 0},
            "toolCalls": [],
        },
        rag={"context": "", "sources": []},
        llm_messages=[],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
        intent_route={"intent": "drawing_analysis"},
    )

    trace = payload.get("drawingAnalysisTrace")

    assert isinstance(trace, dict)
    assert payload["pipeline"]["drawingAnalysisMode"] is True
    assert "drawing:intent:ok" in (payload["pipeline"].get("drawingStages") or [])


def test_extend_pipeline_stages_adds_drawing_tokens():
    trace = ChatDrawingAdminDebugService.build_trace(
        tool_context={"drawingAnalysisMode": True, "toolCalls": []},
        intent_route={"intent": "drawing_analysis"},
        workspace_context={"skills": {"drawingAnalysis": True}},
    )

    stages = ChatDrawingAdminDebugService.extend_pipeline_stages(["tools"], trace)

    assert "tools" in stages
    assert any(stage.startswith("drawing:") for stage in stages)
