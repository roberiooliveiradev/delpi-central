from datetime import datetime, timezone
from uuid import UUID

from app.domain.ports.consent_repository_port import ConsentDTO, ConsentRepositoryPort
from app.infrastructure.db.models.user_consent import UserConsent


class SqlAlchemyConsentRepository(ConsentRepositoryPort):
    def __init__(self, session):
        self._session = session

    @staticmethod
    def _to_dto(row: UserConsent) -> ConsentDTO:
        return ConsentDTO(
            id=row.id,
            user_id=row.user_id,
            purpose=row.purpose,
            granted=row.granted,
            granted_at=row.granted_at,
            revoked_at=row.revoked_at,
        )

    def list_by_user(self, user_id: UUID) -> list[ConsentDTO]:
        rows = self._session.query(UserConsent).filter_by(user_id=user_id).order_by(UserConsent.purpose).all()
        return [self._to_dto(r) for r in rows]

    def get_by_user_and_purpose(self, user_id: UUID, purpose: str):
        row = self._session.query(UserConsent).filter_by(user_id=user_id, purpose=purpose).first()
        return self._to_dto(row) if row else None

    def grant(self, *, user_id: UUID, purpose: str, ip_address: str | None = None, user_agent: str | None = None) -> ConsentDTO:
        now = datetime.now(timezone.utc)
        row = self._session.query(UserConsent).filter_by(user_id=user_id, purpose=purpose).first()
        if row:
            row.granted = True
            row.granted_at = now
            row.revoked_at = None
            row.ip_address = ip_address
            row.user_agent = user_agent
        else:
            row = UserConsent(user_id=user_id, purpose=purpose, granted=True, granted_at=now, ip_address=ip_address, user_agent=user_agent)
            self._session.add(row)
        self._session.flush()
        return self._to_dto(row)

    def revoke(self, user_id: UUID, purpose: str):
        row = self._session.query(UserConsent).filter_by(user_id=user_id, purpose=purpose).first()
        if not row:
            return None
        row.granted = False
        row.revoked_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_dto(row)

    def revoke_all(self, user_id: UUID) -> int:
        now = datetime.now(timezone.utc)
        count = self._session.query(UserConsent).filter_by(user_id=user_id, granted=True).update({"granted": False, "revoked_at": now})
        self._session.flush()
        return count
