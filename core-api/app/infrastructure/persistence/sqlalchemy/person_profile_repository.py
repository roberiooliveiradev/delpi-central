from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.person_profile import PersonProfile
from app.domain.ports.person_profile_repository_port import PersonProfileRepositoryPort
from app.infrastructure.db.models.user_person_profile import UserPersonProfile


class SqlAlchemyPersonProfileRepository(PersonProfileRepositoryPort):
    def __init__(self, session):
        self._session = session

    @staticmethod
    def _to_entity(row: UserPersonProfile) -> PersonProfile:
        return PersonProfile(
            user_id=row.user_id,
            job_title=row.job_title,
            phone_e164=row.phone_e164,
            mobile_e164=row.mobile_e164,
            whatsapp_e164=row.whatsapp_e164,
            photo_storage_key=row.photo_storage_key,
            photo_file_name=row.photo_file_name,
            photo_content_type=row.photo_content_type,
            photo_byte_size=row.photo_byte_size,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get(self, user_id: UUID) -> PersonProfile | None:
        row = self._session.query(UserPersonProfile).filter_by(user_id=user_id).first()
        return self._to_entity(row) if row else None

    def _get_or_create_row(self, user_id: UUID) -> UserPersonProfile:
        row = self._session.query(UserPersonProfile).filter_by(user_id=user_id).first()
        if row:
            return row
        row = UserPersonProfile(user_id=user_id)
        self._session.add(row)
        self._session.flush()
        return row

    def upsert_profile_fields(
        self,
        *,
        user_id: UUID,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> PersonProfile:
        row = self._get_or_create_row(user_id)
        row.job_title = (job_title or "").strip() or None
        row.phone_e164 = phone_e164
        row.mobile_e164 = mobile_e164
        row.whatsapp_e164 = whatsapp_e164
        row.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_entity(row)

    def upsert_photo(
        self,
        *,
        user_id: UUID,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> PersonProfile:
        row = self._get_or_create_row(user_id)
        row.photo_storage_key = storage_key
        row.photo_file_name = file_name
        row.photo_content_type = content_type
        row.photo_byte_size = byte_size
        row.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_entity(row)

    def clear_photo(self, *, user_id: UUID) -> PersonProfile | None:
        row = self._session.query(UserPersonProfile).filter_by(user_id=user_id).first()
        if not row:
            return None
        row.photo_storage_key = None
        row.photo_file_name = None
        row.photo_content_type = None
        row.photo_byte_size = None
        row.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return self._to_entity(row)

    def delete(self, user_id: UUID) -> None:
        self._session.query(UserPersonProfile).filter_by(user_id=user_id).delete()
        self._session.flush()
