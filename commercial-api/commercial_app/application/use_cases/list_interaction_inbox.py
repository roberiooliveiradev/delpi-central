"""Caixa de entrada da sala de interação."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

_INBOX_FILTERS = frozenset({"all", "unread", "mentioned", "process", "wall"})


@dataclass(frozen=True)
class InteractionRoomInboxItem:
    id: UUID
    kind: str
    title: str
    updated_at: datetime
    entity_type: str | None = None
    entity_key: str | None = None
    group_id: UUID | None = None
    unread_count: int = 0
    mentioned: bool = False
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    last_author_user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "kind": self.kind,
            "title": self.title,
            "entity_type": self.entity_type,
            "entity_key": self.entity_key,
            "group_id": str(self.group_id) if self.group_id else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "unread_count": self.unread_count,
            "mentioned": self.mentioned,
            "last_message_preview": self.last_message_preview,
            "last_message_at": (
                self.last_message_at.isoformat() if self.last_message_at else None
            ),
            "last_author_user_id": self.last_author_user_id,
        }


class ListInteractionInboxUseCase:
    """Lista salas do usuário com preview, unread e filtros de inbox."""

    def __init__(
        self,
        *,
        rooms: InteractionRoomRepositoryPort,
        messages: InteractionMessageRepositoryPort,
    ) -> None:
        self._rooms = rooms
        self._messages = messages

    def execute(
        self,
        *,
        actor_user_id: str,
        filter_key: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> list[InteractionRoomInboxItem]:
        actor = (actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        wanted = (filter_key or "all").strip().lower() or "all"
        if wanted not in _INBOX_FILTERS:
            raise ValueError(InteractionRoomContentService.error("kindUnknown"))
        cap = max(1, min(int(limit or 50), 100))
        # Busca um pouco a mais antes dos filtros locais.
        fetch_cap = min(200, max(cap * 3, cap))
        rooms = self._rooms.list_for_user(user_id=actor, limit=fetch_cap, offset=0)
        needle = (query or "").strip().lower()
        items: list[InteractionRoomInboxItem] = []
        for room in rooms:
            if wanted in {"process", "wall"} and room.kind != wanted:
                continue
            if needle and needle not in (room.title or "").lower():
                continue
            member = self._rooms.get_member(room_id=room.id, user_id=actor)
            latest = self._messages.latest_in_room(room.id)
            unread = self._messages.count_unread(
                room_id=room.id,
                since=member.last_read_at if member else None,
                exclude_user_id=actor,
            )
            mentioned = self._messages.user_mentioned_in_room(
                room_id=room.id,
                user_id=actor,
            )
            if wanted == "unread" and unread <= 0:
                continue
            if wanted == "mentioned" and not mentioned:
                continue
            preview = None
            last_at = None
            last_author = None
            if latest is not None:
                preview = " ".join(str(latest.body_text or "").split())
                if len(preview) > 160:
                    preview = preview[:159].rstrip() + "…"
                last_at = latest.created_at
                last_author = latest.author_user_id
            items.append(
                InteractionRoomInboxItem(
                    id=room.id,
                    kind=room.kind,
                    title=room.title,
                    updated_at=room.updated_at,
                    entity_type=room.entity_type,
                    entity_key=room.entity_key,
                    group_id=room.group_id,
                    unread_count=unread,
                    mentioned=mentioned,
                    last_message_preview=preview or None,
                    last_message_at=last_at,
                    last_author_user_id=last_author,
                )
            )
            if len(items) >= cap:
                break
        return items
