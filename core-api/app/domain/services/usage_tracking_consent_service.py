# app/domain/services/usage_tracking_consent_service.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork

USAGE_TRACKING_CONSENT_PURPOSE = "usage_tracking"
BIRTHDAY_NOTIFICATIONS_CONSENT_PURPOSE = "birthday_notifications"
CALLER_APP_HEADER = "X-Delpi-Caller-App"


def user_has_usage_tracking_consent(uow: UnitOfWork, user_id: UUID) -> bool:
    consent = uow.consents.get_by_user_and_purpose(
        user_id,
        USAGE_TRACKING_CONSENT_PURPOSE,
    )
    return bool(consent and consent.granted)


def user_has_birthday_notifications_consent(uow: UnitOfWork, user_id: UUID) -> bool:
    consent = uow.consents.get_by_user_and_purpose(
        user_id,
        BIRTHDAY_NOTIFICATIONS_CONSENT_PURPOSE,
    )
    return bool(consent and consent.granted)
