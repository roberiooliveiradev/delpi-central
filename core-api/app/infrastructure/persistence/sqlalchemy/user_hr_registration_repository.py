"""Core-owned verified mapping. Never derive registration from name or SYS_USR."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.db.models import User, UserHrRegistration


class SqlAlchemyUserHrRegistrationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def validate_registration(value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Matrícula deve ser texto.")
        registration = value.strip()
        if (
            not registration
            or len(registration) > 30
            or any(ch in registration for ch in "/?#\\\r\n\x00")
        ):
            raise ValueError("Matrícula inválida (1-30 caracteres).")
        return registration

    @staticmethod
    def serialize(row: UserHrRegistration | None) -> dict | None:
        if row is None:
            return None
        return {
            "userId": str(row.user_id),
            "registration": row.registration,
            "verifiedAt": row.verified_at.isoformat() if row.verified_at else None,
            "verifiedByUserId": (
                str(row.verified_by_user_id)
                if row.verified_by_user_id else None
            ),
        }

    def get_by_user(self, user_id: UUID) -> UserHrRegistration | None:
        return self.session.get(UserHrRegistration, user_id)

    def get_core_user_ids(self, registrations: set[str]) -> dict[str, str]:
        """Only active Core accounts with an explicitly verified HR mapping."""
        if not registrations:
            return {}
        rows = (
            self.session.query(
                UserHrRegistration.registration, UserHrRegistration.user_id
            )
            .join(User, User.id == UserHrRegistration.user_id)
            .filter(
                UserHrRegistration.registration.in_(registrations),
                UserHrRegistration.verified_at.isnot(None),
                User.active.is_(True),
            )
            .all()
        )
        return {registration: str(user_id) for registration, user_id in rows}

    def get_allocated_registrations(self, user_ids: set[UUID]) -> dict[str, str]:
        """Read registered RH identities for Core users; also block suggestions to occupied users."""
        if not user_ids:
            return {}
        rows = (
            self.session.query(UserHrRegistration.user_id, UserHrRegistration.registration)
            .filter(UserHrRegistration.user_id.in_(user_ids))
            .all()
        )
        return {str(user_id): registration for user_id, registration in rows}

    def upsert(
        self, *, user_id: UUID, registration: str, verified_by_user_id: UUID
    ) -> UserHrRegistration:
        registration = self.validate_registration(registration)
        existing = (
            self.session.query(UserHrRegistration)
            .filter_by(registration=registration)
            .first()
        )
        if existing and existing.user_id != user_id:
            raise ValueError("Matrícula já vinculada a outro usuário.")
        row = self.get_by_user(user_id)
        if row is None:
            row = UserHrRegistration(user_id=user_id, registration=registration)
            self.session.add(row)
        row.registration = registration
        row.verified_by_user_id = verified_by_user_id
        row.verified_at = datetime.now(timezone.utc)
        self.session.flush()
        return row

    def delete(self, user_id: UUID) -> bool:
        row = self.get_by_user(user_id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True
