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
        result = self._uow.consents.revoke(UUID(user_id), purpose)
        self._uow.commit()
        return result


class RevokeAllConsentsUseCase:
    def __init__(self, uow):
        self._uow = uow

    def execute(self, user_id: str) -> int:
        count = self._uow.consents.revoke_all(UUID(user_id))
        self._uow.commit()
        return count
