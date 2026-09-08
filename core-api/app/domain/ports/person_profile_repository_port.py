from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.person_profile import PersonProfile


class PersonProfileRepositoryPort(ABC):
    @abstractmethod
    def get(self, user_id: UUID) -> PersonProfile | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_profile_fields(
        self,
        *,
        user_id: UUID,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> PersonProfile:
        raise NotImplementedError

    @abstractmethod
    def upsert_photo(
        self,
        *,
        user_id: UUID,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> PersonProfile:
        raise NotImplementedError

    @abstractmethod
    def clear_photo(self, *, user_id: UUID) -> PersonProfile | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: UUID) -> None:
        raise NotImplementedError
