from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from commercial_app.domain.entities.attachment import CommercialAttachment


class AttachmentRepositoryPort(ABC):
    @abstractmethod
    def list_for_owner(
        self,
        *,
        owner_type: str,
        owner_id: str,
        limit: int = 50,
    ) -> Sequence[CommercialAttachment]:
        raise NotImplementedError

    @abstractmethod
    def count_for_owners(
        self,
        *,
        owner_type: str,
        owner_ids: Sequence[str],
    ) -> dict[str, int]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, attachment_id: UUID) -> CommercialAttachment | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        *,
        owner_type: str,
        owner_id: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int,
        uploaded_by_user_id: str,
    ) -> CommercialAttachment:
        raise NotImplementedError

    @abstractmethod
    def delete(self, attachment_id: UUID) -> CommercialAttachment | None:
        raise NotImplementedError
