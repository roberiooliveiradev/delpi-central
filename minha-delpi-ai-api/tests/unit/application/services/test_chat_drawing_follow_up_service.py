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


def test_offers_manual_review_chips_when_warnings_present():
    metadata: dict = {}
    drawing = {
        "productCode": "90261877",
        "criticalErrors": 0,
        "errors": 0,
        "warnings": 1,
        "status": "approved_with_notes",
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": drawing},
    )

    labels = [item["label"] for item in metadata.get("drawingFollowUpSuggestions") or []]

    assert "Confirmar revisão manual" in labels
    assert "Descartar ressalva" in labels


def test_offers_bom_reextract_chip_when_bom_issues_and_vision_refinement():
    metadata: dict = {}
    drawing = {
        "productCode": "90263149",
        "criticalErrors": 1,
        "status": "rejected",
        "visionRefinement": {"attempted": True, "columnRowCount": 12},
        "items": [
            {
                "templateKey": "bom_extra",
                "status": "critical_error",
            }
        ],
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": drawing},
    )

    labels = [item["label"] for item in metadata.get("drawingFollowUpSuggestions") or []]

    assert "Reextrair BOM do PDF" in labels


def test_hides_bom_reextract_chip_without_bom_issues():
    metadata: dict = {}
    drawing = {
        "productCode": "90263149",
        "criticalErrors": 0,
        "status": "approved",
        "visionRefinement": {"attempted": True, "columnRowCount": 12},
        "items": [{"templateKey": "bom_match_ok", "status": "ok"}],
    }

    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        metadata,
        intelligence={"drawingAnalysis": drawing},
    )

    labels = [item["label"] for item in metadata.get("drawingFollowUpSuggestions") or []]

    assert "Reextrair BOM do PDF" not in labels
