from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    ROOM_KINDS,
    InteractionRoom,
    InteractionRoomMember,
)
from commercial_app.domain.ports.customer_avatar_repository_port import (
    AuditLogRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)
from commercial_app.domain.services.interaction_room_access_service import (
    InteractionRoomAccessService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

_ACTION_ROOM_DELETED = "interaction_room.deleted"
_ENTITY_INTERACTION_ROOM = "interaction_room"


@dataclass(frozen=True)
class ResolveInteractionRoomInput:
    kind: str
    actor_user_id: str
    entity_type: str | None = None
    entity_key: str | None = None
    group_id: UUID | None = None
    title: str | None = None


class ManageInteractionRoomsUseCase:
    """Resolve lazy, get, participantes e last_read da sala."""

    def __init__(
        self,
        repository: InteractionRoomRepositoryPort,
        audit_repository: AuditLogRepositoryPort | None = None,
    ) -> None:
        self._rooms = repository
        self._access = InteractionRoomAccessService(repository)
        self._audit = audit_repository

    def resolve(self, request: ResolveInteractionRoomInput) -> InteractionRoom:
        actor = (request.actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        kind = (request.kind or "").strip().lower()
        if kind not in ROOM_KINDS:
            raise ValueError(InteractionRoomContentService.error("roomKindInvalid"))

        room: InteractionRoom | None = None
        if kind == "entity":
            entity_type = (request.entity_type or "").strip()
            entity_key = (request.entity_key or "").strip()
            if not entity_type or not entity_key:
                raise ValueError(InteractionRoomContentService.error("entityRequired"))
            if not InteractionMentionKindsContentService.is_known(entity_type):
                raise ValueError(InteractionRoomContentService.error("entityTypeUnknown"))
            room = self._rooms.find_entity_room(
                entity_type=entity_type,
                entity_key=entity_key,
            )
            if room is None:
                title = (request.title or "").strip() or f"{entity_type}:{entity_key}"
                room = self._rooms.create_room(
                    kind="entity",
                    title=title,
                    created_by_user_id=actor,
                    entity_type=entity_type,
                    entity_key=entity_key,
                )
        elif kind == "wall":
            room = self._rooms.find_wall_room(group_id=request.group_id)
            if room is None:
                if request.group_id is None:
                    title = (
                        (request.title or "").strip()
                        or InteractionRoomContentService.message("wallGlobalTitle")
                    )
                else:
                    title = (request.title or "").strip() or f"wall:{request.group_id}"
                room = self._rooms.create_room(
                    kind="wall",
                    title=title,
                    created_by_user_id=actor,
                    group_id=request.group_id,
                )
        else:
            # process — sem único parcial; sempre cria nova se title/keys distintos
            entity_type = (request.entity_type or "").strip() or None
            entity_key = (request.entity_key or "").strip() or None
            title = (request.title or "").strip()
            if not title:
                title = entity_key or entity_type or "process"
            room = self._rooms.create_room(
                kind="process",
                title=title,
                created_by_user_id=actor,
                entity_type=entity_type,
                entity_key=entity_key,
            )

        self._rooms.add_member(room_id=room.id, user_id=actor, role="member")
        return self._rooms.get_by_id(room.id) or room

    def get(self, *, room_id: UUID, actor_user_id: str) -> InteractionRoom:
        _ = (actor_user_id or "").strip()
        return self._access.require_room_exists(room_id)

    def list_members(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
    ) -> Sequence[InteractionRoomMember]:
        _ = (actor_user_id or "").strip()
        room = self._access.require_room_exists(room_id)
        return self._rooms.list_members(room.id)

    def add_member(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
        user_id: str,
        role: str = "member",
    ) -> InteractionRoomMember:
        room = self._access.require_room_exists(room_id)
        _ = (actor_user_id or "").strip()
        target = (user_id or "").strip()
        if not target:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        return self._rooms.add_member(
            room_id=room.id,
            user_id=target,
            role=(role or "member").strip() or "member",
        )

    def remove_member(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
        user_id: str,
    ) -> None:
        room = self._access.require_room_exists(room_id)
        _ = (actor_user_id or "").strip()
        target = (user_id or "").strip()
        if not target:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        removed = self._rooms.remove_member(room_id=room.id, user_id=target)
        if not removed:
            raise LookupError(InteractionRoomContentService.error("roomNotFound"))

    def mark_read(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
        read_at: datetime | None = None,
    ) -> InteractionRoomMember:
        room = self._access.require_room_exists(room_id)
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        member = self._rooms.mark_read(
            room_id=room.id,
            user_id=actor,
            read_at=read_at,
        )
        if member is None:
            raise RuntimeError("Falha ao marcar sala como lida.")
        return member

    def soft_delete(
        self,
        *,
        room_id: UUID,
        actor_user_id: str,
    ) -> InteractionRoom:
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        room = self._access.require_room_exists(room_id)
        deleted = self._rooms.soft_delete(room_id=room.id)
        if deleted is None:
            raise LookupError(InteractionRoomContentService.error("roomNotFound"))
        self._append_audit(actor_user_id=actor, room=deleted)
        return deleted

    def _append_audit(self, *, actor_user_id: str, room: InteractionRoom) -> None:
        if self._audit is None:
            return
        payload: dict[str, Any] = {
            "title": room.title,
            "kind": room.kind,
            "entity_type": room.entity_type,
            "entity_key": room.entity_key,
            "group_id": str(room.group_id) if room.group_id else None,
        }
        self._audit.append(
            actor_user_id=actor_user_id,
            action=_ACTION_ROOM_DELETED,
            entity_type=_ENTITY_INTERACTION_ROOM,
            entity_id=str(room.id),
            payload=payload,
        )
