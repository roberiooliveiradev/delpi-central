from app.application.services.chat_session_memory_metrics_service import (
    ChatSessionMemoryMetricsService,
)


def test_build_snapshot_with_follow_up():
    snapshot = {
        "memoryUsed": True,
        "lastEntities": {"productCode": "10080001", "period": "last_30_days"},
        "resolvedReferences": [{"text": "follow-up", "value": "10080001"}],
        "preferencesApplied": ["format=table"],
        "followUpDetected": True,
        "followUpType": "supplier",
        "lastAction": {"name": "stock_lookup", "params": {"productCode": "10080001"}},
    }

    metrics = ChatSessionMemoryMetricsService.build_snapshot(snapshot)

    assert metrics is not None
    assert metrics["hasProductCode"] is True
    assert metrics["hasPeriod"] is True
    assert metrics["resolvedReferenceCount"] == 1
    assert metrics["lastActionName"] == "stock_lookup"


def test_attach_to_metadata():
    metadata: dict = {}
    ChatSessionMemoryMetricsService.attach_to_assistant_metadata(
        metadata,
        snapshot={"memoryUsed": True, "lastEntities": {"productCode": "1"}},
    )

    assert metadata["sessionMemoryMetrics"]["entityCount"] == 1
