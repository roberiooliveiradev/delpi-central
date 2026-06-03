from app.domain.services.chat_memory_context_loss_alert_service import (
    ChatMemoryContextLossAlertService,
)


def test_build_turn_alerts_on_low_score_and_flags():
    alerts = ChatMemoryContextLossAlertService.build_turn_alerts(
        assertiveness={
            "score": 45,
            "flags": ["follow_up_without_entity_reuse", "unnecessary_code_request"],
        },
        snapshot={"memoryAmbiguity": {"candidates": ["1001", "1002"]}},
    )

    codes = {item["code"] for item in alerts}

    assert "follow_up_without_entity_reuse" in codes
    assert "unnecessary_code_request" in codes
    assert "low_assertiveness" in codes
    assert "memory_ambiguity" in codes


def test_attach_to_metadata():
    metadata: dict = {}

    ChatMemoryContextLossAlertService.attach_to_metadata(
        metadata,
        assertiveness={"score": 40, "flags": ["stale_product_context"]},
    )

    assert metadata["memoryContextAlerts"]
    assert metadata["memoryContextAlerts"][0]["code"] == "stale_product_context"
