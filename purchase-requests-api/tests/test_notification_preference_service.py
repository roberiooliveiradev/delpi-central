from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.infrastructure.persistence.repositories.notification_subscription_repository import (
    NotificationSubscriptionRepository,
)
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


def test_portal_users_for_protheus_event_filters_by_subscription() -> None:
    mapping_repo = UserProtheusMappingRepository()
    subscription_repo = NotificationSubscriptionRepository()
    portal_user = "pref-test-portal-user"
    mapping_repo.upsert_mapping(
        user_id=portal_user,
        protheus_user_id="TOTVS01",
        protheus_user_code=None,
        mapping_status="mapped",
        mapping_source="manual",
        verified=True,
    )
    subscription_repo.replace_for_user(
        portal_user,
        [
            {"event_key": "purchase_order_created", "enabled": True},
            {"event_key": "purchase_receipt_recorded", "enabled": False},
        ],
    )

    service = PurchaseRequestNotificationPreferenceService(
        subscription_repository=subscription_repo,
        mapping_repository=mapping_repo,
    )
    order_users = service.portal_users_for_protheus_event(
        protheus_user_id="TOTVS01",
        event_key="purchase_order_created",
    )
    receipt_users = service.portal_users_for_protheus_event(
        protheus_user_id="TOTVS01",
        event_key="purchase_receipt_recorded",
    )
    assert portal_user in order_users
    assert portal_user not in receipt_users
