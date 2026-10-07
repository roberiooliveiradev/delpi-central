from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


def test_portal_users_for_mapped_requester_resolves_identity() -> None:
    mapping_repo = UserProtheusMappingRepository()
    portal_user = "pref-test-portal-user"
    mapping_repo.upsert_mapping(
        user_id=portal_user,
        protheus_user_id="TOTVS01",
        protheus_user_code=None,
        mapping_status="mapped",
        mapping_source="manual",
        verified=True,
    )

    service = PurchaseRequestNotificationPreferenceService(
        mapping_repository=mapping_repo,
    )

    assert service.portal_users_for_mapped_requester("TOTVS01") == [portal_user]
    assert service.portal_users_for_mapped_requester("UNKNOWN") == []
    assert service.portal_users_for_mapped_requester("") == []
