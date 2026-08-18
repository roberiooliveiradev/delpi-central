from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID, uuid4

import pytest

from commercial_app.application.use_cases.manage_interaction_rooms import (
    ManageInteractionRoomsUseCase,
    ResolveInteractionRoomInput,
)
from commercial_app.domain.entities.interaction_room import (
    InteractionRoom,
    InteractionRoomMember,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


class InMemoryInteractionRoomRepo(InteractionRoomRepositoryPort):
    def __init__(self) -> None:
        self.rooms: dict[UUID, InteractionRoom] = {}
        self.members: dict[tuple[UUID, str], InteractionRoomMember] = {}

    def get_by_id(self, room_id: UUID) -> InteractionRoom | None:
        room = self.rooms.get(room_id)
        if room is None or room.deleted_at is not None:
            return None
        return room

    def find_entity_room(
        self,
        *,
        entity_type: str,
        entity_key: str,
    ) -> InteractionRoom | None:
        for room in self.rooms.values():
            if (
                room.deleted_at is None
                and room.kind == "entity"
                and room.entity_type == entity_type
                and room.entity_key == entity_key
            ):
                return room
        return None

    def find_wall_room(self, *, group_id: UUID | None = None) -> InteractionRoom | None:
        for room in self.rooms.values():
            if (
                room.deleted_at is None
                and room.kind == "wall"
                and room.group_id == group_id
            ):
                return room
        return None

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
        now = datetime.now(timezone.utc)
        room = InteractionRoom(
            id=uuid4(),
            kind=kind,
            title=title,
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
            entity_type=entity_type,
            entity_key=entity_key,
            group_id=group_id,
        )
        self.rooms[room.id] = room
        return room

    def touch_updated_at(self, room_id: UUID) -> InteractionRoom | None:
        room = self.get_by_id(room_id)
        if room is None:
            return None
        updated = InteractionRoom(
            id=room.id,
            kind=room.kind,
            title=room.title,
            created_by_user_id=room.created_by_user_id,
            created_at=room.created_at,
            updated_at=datetime.now(timezone.utc),
            entity_type=room.entity_type,
            entity_key=room.entity_key,
            group_id=room.group_id,
            deleted_at=room.deleted_at,
        )
        self.rooms[room.id] = updated
        return updated

    def list_for_user(
        self,
        *,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InteractionRoom]:
        items = [
            self.rooms[room_id]
            for (room_id, uid), member in self.members.items()
            if uid == user_id and room_id in self.rooms
        ]
        return items[offset : offset + limit]

    def list_members(self, room_id: UUID) -> Sequence[InteractionRoomMember]:
        return [
            member
            for (rid, _), member in self.members.items()
            if rid == room_id
        ]

    def get_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
    ) -> InteractionRoomMember | None:
        return self.members.get((room_id, user_id))

    def add_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
        role: str = "member",
    ) -> InteractionRoomMember:
        existing = self.members.get((room_id, user_id))
        if existing is not None:
            return existing
        member = InteractionRoomMember(
            id=uuid4(),
            room_id=room_id,
            user_id=user_id,
            role=role,
            created_at=datetime.now(timezone.utc),
        )
        self.members[(room_id, user_id)] = member
        return member

    def remove_member(self, *, room_id: UUID, user_id: str) -> bool:
        return self.members.pop((room_id, user_id), None) is not None

    def mark_read(
        self,
        *,
        room_id: UUID,
        user_id: str,
        read_at: datetime | None = None,
    ) -> InteractionRoomMember | None:
        member = self.members.get((room_id, user_id))
        if member is None:
            return None
        updated = InteractionRoomMember(
            id=member.id,
            room_id=member.room_id,
            user_id=member.user_id,
            role=member.role,
            created_at=member.created_at,
            last_read_at=read_at or datetime.now(timezone.utc),
            muted=member.muted,
        )
        self.members[(room_id, user_id)] = updated
        return updated


def test_resolve_entity_is_idempotent_and_adds_member() -> None:
    repo = InMemoryInteractionRoomRepo()
    uc = ManageInteractionRoomsUseCase(repo)
    first = uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|102942",
            actor_user_id="u1",
            title="Pedido 102942",
        )
    )
    second = uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|102942",
            actor_user_id="u2",
        )
    )
    assert first.id == second.id
    assert repo.get_member(room_id=first.id, user_id="u1") is not None
    assert repo.get_member(room_id=first.id, user_id="u2") is not None


def test_get_requires_membership() -> None:
    repo = InMemoryInteractionRoomRepo()
    uc = ManageInteractionRoomsUseCase(repo)
    room = uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="customer",
            entity_key="0001|01",
            actor_user_id="u1",
        )
    )
    assert uc.get(room_id=room.id, actor_user_id="u1").id == room.id
    with pytest.raises(PermissionError) as exc:
        uc.get(room_id=room.id, actor_user_id="stranger")
    assert str(exc.value) == InteractionRoomContentService.error("accessDenied")


def test_mark_read_and_members() -> None:
    repo = InMemoryInteractionRoomRepo()
    uc = ManageInteractionRoomsUseCase(repo)
    room = uc.resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            entity_type="order",
            entity_key="01|1",
            actor_user_id="u1",
        )
    )
    uc.add_member(room_id=room.id, actor_user_id="u1", user_id="u2")
    members = uc.list_members(room_id=room.id, actor_user_id="u1")
    assert {m.user_id for m in members} == {"u1", "u2"}
    read = uc.mark_read(room_id=room.id, actor_user_id="u1")
    assert read.last_read_at is not None


def test_resolve_rejects_unknown_entity_type() -> None:
    uc = ManageInteractionRoomsUseCase(InMemoryInteractionRoomRepo())
    with pytest.raises(ValueError) as exc:
        uc.resolve(
            ResolveInteractionRoomInput(
                kind="entity",
                entity_type="spaceship",
                entity_key="x",
                actor_user_id="u1",
            )
        )
    assert str(exc.value) == InteractionRoomContentService.error("entityTypeUnknown")
