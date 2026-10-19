from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user_protheus_identity import UserProtheusIdentity


class UserProtheusIdentityRepositoryPort(ABC):
    @abstractmethod
    def get(self, user_id: UUID) -> UserProtheusIdentity | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_protheus_user_id(
        self,
        protheus_user_id: str,
    ) -> UserProtheusIdentity | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_ids(
        self,
        user_ids: list[UUID],
    ) -> list[UserProtheusIdentity]:
        raise NotImplementedError

    @abstractmethod
    def list_page(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[UserProtheusIdentity], int]:
        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        *,
        user_id: UUID,
        protheus_user_id: str | None,
        protheus_user_code: str | None,
        mapping_status: str,
        mapping_source: str | None,
        verified: bool,
        updated_by_user_id: UUID | None,
    ) -> UserProtheusIdentity:
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: UUID) -> None:
        raise NotImplementedError
