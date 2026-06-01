from app.domain.services.chat_error_handling_admin_metrics_service import (
    ChatErrorHandlingAdminMetricsService,
)


def test_snapshot_from_metadata():
    snapshot = ChatErrorHandlingAdminMetricsService.snapshot_from_metadata(
        {
            "errorHandling": {
                "type": "empty_result",
                "severity": "warning",
                "recoverable": True,
                "apiFailed": False,
                "suggestions": ["A", "B"],
            }
        }
    )

    assert snapshot is not None
    assert snapshot["type"] == "empty_result"
    assert snapshot["suggestionCount"] == 2


def test_aggregate_by_type():
    summary = ChatErrorHandlingAdminMetricsService.aggregate(
        entries=[
            {
                "loggedAt": "2026-06-01T12:00:00Z",
                "snapshot": {
                    "type": "empty_result",
                    "recoverable": True,
                    "apiFailed": False,
                    "hasAutoRecovery": True,
                },
            },
            {
                "loggedAt": "2026-06-01T12:01:00Z",
                "snapshot": {
                    "type": "api_unavailable",
                    "recoverable": True,
                    "apiFailed": True,
                    "hasAutoRecovery": False,
                },
            },
        ],
        recovery_clicks=[{"snapshot": {"group": "recuperar", "label": "Tentar novamente"}}],
        recovery_attempts=[{"snapshot": {"strategy": "retry_last", "ok": True}}],
        hours=24,
        since_iso="2026-06-01T00:00:00Z",
    )

    assert summary["totalEvents"] == 2
    assert summary["apiFailedCount"] == 1
    assert summary["autoRecoveryPlans"] == 1
    assert summary["recoveryClicksCount"] == 1
    assert summary["recoveryAttemptsCount"] == 1
    assert summary["recoverySuccessCount"] == 1
    assert summary["byType"][0]["type"] == "empty_result"
