from app.domain.services.chat_session_memory_admin_metrics_service import (
    ChatSessionMemoryAdminMetricsService,
)


def test_snapshot_from_metadata_merges_metrics_and_assertiveness():
    snapshot = ChatSessionMemoryAdminMetricsService.snapshot_from_metadata(
        {
            "sessionMemoryMetrics": {
                "memoryUsed": True,
                "entityCount": 2,
                "followUpDetected": True,
            },
            "contextAssertiveness": {
                "score": 55.0,
                "flags": ["follow_up_without_entity_reuse"],
                "followUpResolved": False,
            },
        }
    )

    assert snapshot is not None
    assert snapshot["entityCount"] == 2
    assert snapshot["contextLossRisk"] is True
    assert "follow_up_without_entity_reuse" in snapshot["assertivenessFlags"]


def test_aggregate_snapshots_counts_risk_turns():
    usage = ChatSessionMemoryAdminMetricsService.aggregate_snapshots(
        [
            {
                "loggedAt": "2026-06-01T12:00:00Z",
                "snapshot": {
                    "memoryUsed": True,
                    "entityCount": 1,
                    "followUpDetected": True,
                    "followUpResolved": False,
                    "contextLossRisk": True,
                    "assertivenessScore": 50,
                    "assertivenessFlags": ["follow_up_without_entity_reuse"],
                },
            },
            {
                "loggedAt": "2026-06-01T12:05:00Z",
                "snapshot": {
                    "memoryUsed": True,
                    "entityCount": 1,
                    "followUpDetected": True,
                    "followUpResolved": True,
                    "contextLossRisk": False,
                    "assertivenessScore": 95,
                    "assertivenessFlags": ["follow_up_entity_reused"],
                },
            },
        ],
        hours=24,
        since_iso="2026-05-31T12:00:00Z",
    )

    assert usage["memoryTurnsCount"] == 2
    assert usage["contextLossRiskTurns"] == 1
    assert usage["followUpResolutionRate"] == 0.5
    assert usage["lowAssertivenessTurns"] == 1


def test_aggregate_feedback_memory_reasons():
    feedback = ChatSessionMemoryAdminMetricsService.aggregate_feedback_rows(
        [
            {
                "messageId": "m1",
                "rating": -1,
                "reason": "memory_forgot_product",
                "contextMetadata": {"usedMemory": True},
                "createdAt": "2026-06-01T12:00:00Z",
            },
            {
                "messageId": "m2",
                "rating": -1,
                "reason": "memory_forgot_product",
                "contextMetadata": {"usedMemory": True},
                "createdAt": "2026-06-01T12:01:00Z",
            },
            {
                "messageId": "m3",
                "rating": -1,
                "reason": "memory_forgot_product",
                "contextMetadata": {"usedMemory": True},
                "createdAt": "2026-06-01T12:02:00Z",
            },
        ]
    )

    assert feedback["lostContextFeedbackCount"] == 3
    assert any(alert["code"] == "context_loss" for alert in feedback["alerts"])
