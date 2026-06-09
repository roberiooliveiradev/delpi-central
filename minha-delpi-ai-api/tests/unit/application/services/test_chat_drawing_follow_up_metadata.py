from app.application.services.chat_drawing_follow_up_service import (
    ChatDrawingFollowUpService,
)


def test_attach_promotes_drawing_fields_to_top_level_metadata():
    metadata: dict = {}
    tool_context = {
        "drawingAnalysisMode": True,
        "drawingAnalysis": {"productCode": "90260140", "items": [{"status": "ok"}]},
        "drawingAnalysisExport": {
            "markdown": "# Relatório de Análise de Desenho DELPI",
            "filename": "relatorio.md",
            "mimeType": "text/markdown",
        },
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": tool_context["drawingAnalysis"]},
        tool_context=tool_context,
        latency_ms=1200,
    )

    assert metadata["drawingAnalysisMode"] is True
    assert metadata["drawingAnalysisExport"]["markdown"].startswith("# Relatório")
    assert metadata["drawingAnalysis"]["productCode"] == "90260140"
