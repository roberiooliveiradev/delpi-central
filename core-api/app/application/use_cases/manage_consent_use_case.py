from uuid import UUID


class GrantConsentUseCase:
    def __init__(self, uow):
        self._uow = uow

    def execute(self, *, user_id: str, purpose: str, ip_address: str | None = None, user_agent: str | None = None):
        result = self._uow.consents.grant(
            user_id=UUID(user_id),
            purpose=purpose,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()
        return result


class RevokeConsentUseCase:
    def __init__(self, uow):
        self._uow = uow

    def execute(self, *, user_id: str, purpose: str):
        from app.domain.services.usage_tracking_consent_service import (
            USAGE_TRACKING_CONSENT_PURPOSE,
        )

        result = self._uow.consents.revoke(UUID(user_id), purpose)

        if purpose == USAGE_TRACKING_CONSENT_PURPOSE:
            from app.application.services.usage_tracking_purge_service import (
                purge_usage_tracking_data,
            )

            purge_usage_tracking_data(self._uow, user_id=UUID(user_id))

        self._uow.commit()
        return result


class RevokeAllConsentsUseCase:
    def __init__(self, uow):
        self._uow = uow

    def execute(self, user_id: str) -> int:
        from app.domain.services.usage_tracking_consent_service import (
            USAGE_TRACKING_CONSENT_PURPOSE,
        )

        uid = UUID(user_id)
        had_usage_tracking = bool(
            self._uow.consents.get_by_user_and_purpose(uid, USAGE_TRACKING_CONSENT_PURPOSE)
        )
        count = self._uow.consents.revoke_all(uid)

        if had_usage_tracking:
            from app.application.services.usage_tracking_purge_service import (
                purge_usage_tracking_data,
            )

            purge_usage_tracking_data(self._uow, user_id=uid)

        self._uow.commit()
        return count
