from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    InteractionRoom,
    InteractionRoomMember,
)


class InteractionRoomRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, room_id: UUID) -> InteractionRoom | None:
        raise NotImplementedError

    @abstractmethod
    def find_entity_room(
        self,
        *,
        entity_type: str,
        entity_key: str,
    ) -> InteractionRoom | None:
        raise NotImplementedError

    @abstractmethod
    def find_wall_room(self, *, group_id: UUID | None = None) -> InteractionRoom | None:
        raise NotImplementedError

    @abstractmethod
    def create_room(
        self,
        *,
        kind: str,
        title: str,
        created_by_user_id: str,
        entity_type: str | None = None,
        entity_key: str | None = None,
        group_id: UUID | None = None,
    ) -> InteractionRoom:
        raise NotImplementedError

    @abstractmethod
    def touch_updated_at(self, room_id: UUID) -> InteractionRoom | None:
        raise NotImplementedError

    @abstractmethod
    def list_for_user(
        self,
        *,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InteractionRoom]:
        raise NotImplementedError

    @abstractmethod
    def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InteractionRoom]:
        raise NotImplementedError

    @abstractmethod
    def list_members(self, room_id: UUID) -> Sequence[InteractionRoomMember]:
        raise NotImplementedError

    @abstractmethod
    def get_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
    ) -> InteractionRoomMember | None:
        raise NotImplementedError

    @abstractmethod
    def add_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
        role: str = "member",
    ) -> InteractionRoomMember:
        raise NotImplementedError

    @abstractmethod
    def remove_member(self, *, room_id: UUID, user_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mark_read(
        self,
        *,
        room_id: UUID,
        user_id: str,
        read_at: datetime | None = None,
    ) -> InteractionRoomMember | None:
        raise NotImplementedError
