from app.application.services.chat_drawing_metrics_service import (
    ChatDrawingMetricsService,
)


def test_aggregate_snapshots_empty():
    result = ChatDrawingMetricsService.aggregate_snapshots(
        [],
        hours=24,
        since_iso="2026-05-30T00:00:00+00:00",
    )

    assert result["analysesCount"] == 0
    assert result["byStatus"] == {}
    assert result["recent"] == []


def test_aggregate_snapshots_counts():
    entries = [
        {
            "loggedAt": "2026-05-31T10:00:00+00:00",
            "action": "chat.message.sent",
            "snapshot": {
                "productCode": "90260140",
                "overallStatus": "rejected",
                "criticalErrors": 2,
                "errors": 0,
                "reportExported": True,
                "analyserOk": True,
                "hasPdfAttachment": True,
            },
        },
        {
            "loggedAt": "2026-05-31T11:00:00+00:00",
            "action": "chat.message.streamed",
            "snapshot": {
                "productCode": "90264130",
                "overallStatus": "approved",
                "criticalErrors": 0,
                "errors": 0,
                "reportExported": False,
                "analyserOk": False,
                "hasPdfAttachment": False,
            },
        },
    ]

    result = ChatDrawingMetricsService.aggregate_snapshots(
        entries,
        hours=168,
        since_iso="2026-05-24T00:00:00+00:00",
    )

    assert result["analysesCount"] == 2
    assert result["uniqueProductCodes"] == 2
    assert result["byStatus"]["rejected"] == 1
    assert result["byStatus"]["approved"] == 1
    assert result["totalCriticalErrors"] == 2
    assert result["reportExportedCount"] == 1
    assert len(result["recent"]) == 2
