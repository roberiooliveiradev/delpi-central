from __future__ import annotations

import pytest

from purchase_requests_app.infrastructure.persistence.repositories.notification_subscription_repository import (
    NotificationSubscriptionRepository,
)


def test_replace_notification_subscriptions_persists_enabled_events() -> None:
    repo = NotificationSubscriptionRepository()
    user_id = "admin-test-user-notifications"
    items = repo.replace_for_user(
        user_id,
        [
            {"event_key": "purchase_order_created", "enabled": True},
            {"event_key": "purchase_receipt_recorded", "enabled": False},
            {"event_key": "purchase_delivery_overdue", "enabled": True},
        ],
    )
    enabled = {row["event_key"] for row in items if row["enabled"]}
    assert enabled == {"purchase_order_created", "purchase_delivery_overdue"}

    replaced = repo.replace_for_user(
        user_id,
        [{"event_key": "purchase_request_approved", "enabled": True}],
    )
    assert len(replaced) == 1
    assert replaced[0]["event_key"] == "purchase_request_approved"


def test_replace_notification_subscriptions_rejects_invalid_event() -> None:
    repo = NotificationSubscriptionRepository()
    with pytest.raises(ValueError, match="inválido"):
        repo.replace_for_user(
            "admin-test-invalid-event",
            [{"event_key": "not_a_real_event", "enabled": True}],
        )
