from app.domain.services.chat_text_task_admin_metrics_service import (
    ChatTextTaskAdminMetricsService,
)


def test_snapshot_from_metadata_with_mixed_and_quality():
    metadata = {
        "textTaskMetrics": {"type": "correction", "subtype": "text_correct", "tone": "formal"},
        "textTaskMixed": {"textCategory": "email", "draftAttached": True},
        "textTaskQuality": {"passed": False, "checks": [{"code": "x"}]},
        "textCanvasVersions": [{"version": 1}, {"version": 2}],
    }

    snapshot = ChatTextTaskAdminMetricsService.snapshot_from_metadata(metadata)

    assert snapshot["subtype"] == "text_correct"
    assert snapshot["mixed"] is True
    assert snapshot["qualityPassed"] is False
    assert snapshot["canvasVersionCount"] == 2


def test_enrich_audit_metadata():
    audit = {}

    ChatTextTaskAdminMetricsService.enrich_audit_metadata(
        audit,
        assistant_metadata={"textTaskMetrics": {"subtype": "text_summarize", "type": "summary"}},
    )

    assert audit["textTaskMetrics"]["subtype"] == "text_summarize"


def test_aggregate_snapshots():
    entries = [
        {
            "loggedAt": "2026-05-30T12:00:00Z",
            "snapshot": {"subtype": "text_correct", "type": "correction", "mixed": True},
        },
        {
            "loggedAt": "2026-05-30T11:00:00Z",
            "snapshot": {"subtype": "text_email_create", "type": "email", "qualityPassed": False},
        },
    ]

    result = ChatTextTaskAdminMetricsService.aggregate_snapshots(
        entries,
        hours=24,
        since_iso="2026-05-29T12:00:00Z",
    )

    assert result["textTasksCount"] == 2
    assert result["mixedTurnCount"] == 1
    assert result["qualityFailedCount"] == 1
    assert result["bySubtype"]["text_correct"] == 1
