from app.application.services.chat_drawing_follow_up_service import (
    ChatDrawingFollowUpService,
)


def test_attach_drawing_follow_up_with_critical_errors():
    metadata: dict = {}
    drawing = {
        "productCode": "90260140",
        "criticalErrors": 2,
        "status": "rejected",
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": drawing},
        tool_context={
            "drawingAnalysisExport": {
                "filename": "relatorio-desenho-90260140-20260530.md",
                "mimeType": "text/markdown",
                "markdown": "# Relatório",
            }
        },
    )

    labels = [item["label"] for item in metadata.get("drawingFollowUpSuggestions") or []]

    assert "Ver só erros críticos" in labels
    assert metadata.get("drawingAnalysisExport", {}).get("filename")


def test_attach_hides_critical_chip_when_no_errors():
    metadata: dict = {}
    drawing = {"productCode": "90260140", "criticalErrors": 0, "status": "approved"}

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": drawing},
    )

    labels = [item["label"] for item in metadata.get("drawingFollowUpSuggestions") or []]

    assert "Ver só erros críticos" not in labels
    assert "Ver checklist completo" in labels
