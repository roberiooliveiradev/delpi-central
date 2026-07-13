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
    assert labels.index("Confirmar revisão manual") < labels.index("Gerar relatório")


def test_offers_manual_review_when_pending_items_even_with_critical():
    """Screenshot 90261823: conclusão rejeitada + pendentes — atalho deve aparecer na frente."""
    drawing = {
        "productCode": "90261823",
        "criticalErrors": 1,
        "errors": 0,
        "warnings": 2,
        "status": "rejected",
        "items": [
            {"templateKey": "bom_extra", "status": "critical_error"},
            {"templateKey": "balloon_missing_codes", "status": "pending"},
            {"templateKey": "segment_length_pending", "status": "pending"},
        ],
    }

    labels = [
        item["label"] for item in ChatDrawingFollowUpService.build_suggestions(drawing)
    ]

    assert labels[0] == "Confirmar revisão manual"
    assert "Descartar ressalva" in labels
    assert "Ver só erros críticos" in labels
    # max 6 chips — «Gerar relatório» pode cair fora; o atalho de revisão fica na frente.
    assert labels.index("Confirmar revisão manual") < labels.index("Validar BOM")


def test_manual_review_from_pending_items_when_warning_counter_desynced():
    drawing = {
        "productCode": "90261823",
        "criticalErrors": 0,
        "errors": 0,
        "warnings": 0,
        "status": "approved",
        "items": [
            {"templateKey": "balloon_missing_codes", "status": "pending"},
            {"templateKey": "segment_length_pending", "status": "pending"},
        ],
    }

    labels = [
        item["label"] for item in ChatDrawingFollowUpService.build_suggestions(drawing)
    ]

    assert "Confirmar revisão manual" in labels


def test_manual_review_hidden_when_only_critical_no_adjustable():
    drawing = {
        "productCode": "90260140",
        "criticalErrors": 1,
        "errors": 0,
        "warnings": 0,
        "status": "rejected",
        "items": [{"templateKey": "bom_extra", "status": "critical_error"}],
    }

    labels = [
        item["label"] for item in ChatDrawingFollowUpService.build_suggestions(drawing)
    ]

    assert "Confirmar revisão manual" not in labels
    assert "Descartar ressalva" not in labels


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
