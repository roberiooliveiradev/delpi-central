from __future__ import annotations

from abc import ABC, abstractmethod

from commercial_app.domain.entities.user_profile import CommercialUserProfile


class UserProfileRepositoryPort(ABC):
    @abstractmethod
    def get(self, user_id: str) -> CommercialUserProfile | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_job_title(self, *, user_id: str, job_title: str | None) -> CommercialUserProfile:
        raise NotImplementedError

    @abstractmethod
    def upsert_photo(
        self,
        *,
        user_id: str,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> CommercialUserProfile:
        raise NotImplementedError

    @abstractmethod
    def clear_photo(self, *, user_id: str) -> CommercialUserProfile | None:
        raise NotImplementedError
