from app.application.services.chat_document_vision_metrics_service import (
    ChatDocumentVisionMetricsService,
)


def test_build_snapshot():
    snapshot = ChatDocumentVisionMetricsService.build_snapshot(
        {
            "engine": "tesseract",
            "stages": ["native", "tesseract"],
            "legibilityScore": 0.82,
            "durationMs": 1200,
            "schemaVersion": "1",
        },
        char_count=500,
        legible=True,
        context="drawing",
    )

    assert snapshot["engine"] == "tesseract"
    assert snapshot["stageCount"] == 2
    assert snapshot["charCount"] == 500
    assert snapshot["legible"] is True
    assert snapshot["context"] == "drawing"


def test_attach_to_assistant_metadata_from_tool_context():
    metadata: dict = {}
    tool_context = {
        "drawingAnalysisMode": True,
        "documentVision": {
            "engine": "auto",
            "stages": ["native", "tesseract"],
            "durationMs": 800,
        },
        "drawingPdfExtractSummary": {"legible": True, "charCount": 120},
    }

    ChatDocumentVisionMetricsService.attach_to_assistant_metadata(
        metadata,
        tool_context=tool_context,
    )

    metrics = metadata.get("documentVisionMetrics")

    assert metrics["engine"] == "auto"
    assert metrics["charCount"] == 120
    assert metrics["legible"] is True


def test_enrich_audit_metadata():
    audit = {}
    enriched = ChatDocumentVisionMetricsService.enrich_audit_metadata(
        audit,
        tool_context={
            "documentVision": {"engine": "tesseract", "stages": ["tesseract"]},
        },
    )

    assert enriched["documentVision"]["engine"] == "tesseract"


def test_aggregate_snapshots():
    result = ChatDocumentVisionMetricsService.aggregate_snapshots(
        [
            {
                "loggedAt": "2026-05-31T12:00:00Z",
                "action": "chat.message.sent",
                "snapshot": {
                    "engine": "tesseract",
                    "context": "drawing",
                    "legible": True,
                    "durationMs": 1000,
                },
            },
            {
                "loggedAt": "2026-05-31T11:00:00Z",
                "action": "chat.message.streamed",
                "snapshot": {
                    "engine": "native",
                    "context": "attachment",
                    "legible": False,
                    "durationMs": 200,
                },
            },
        ],
        hours=24,
        since_iso="2026-05-30T12:00:00Z",
    )

    assert result["runsCount"] == 2
    assert result["byEngine"]["tesseract"] == 1
    assert result["legibleCount"] == 1
    assert result["legibilityRate"] == 0.5
    assert len(result["recent"]) == 2
