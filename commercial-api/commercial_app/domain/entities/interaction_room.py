from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID


ROOM_KINDS = frozenset({"entity", "process", "wall"})
MEMBER_ROLES = frozenset({"member", "watcher"})
MESSAGE_KINDS = frozenset({"text", "system", "task_ref", "pin"})


@dataclass(frozen=True)
class InteractionRoom:
    id: UUID
    kind: str
    title: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime
    entity_type: str | None = None
    entity_key: str | None = None
    group_id: UUID | None = None
    deleted_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "kind": self.kind,
            "entity_type": self.entity_type,
            "entity_key": self.entity_key,
            "group_id": str(self.group_id) if self.group_id else None,
            "title": self.title,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


@dataclass(frozen=True)
class InteractionRoomMember:
    id: UUID
    room_id: UUID
    user_id: str
    role: str
    created_at: datetime
    last_read_at: datetime | None = None
    muted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "user_id": self.user_id,
            "role": self.role,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
            "muted": self.muted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class InteractionMention:
    id: UUID
    message_id: UUID
    mention_kind: str
    ref: Mapping[str, Any]
    label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "mention_kind": self.mention_kind,
            "ref": dict(self.ref),
            "label": self.label,
        }


@dataclass(frozen=True)
class InteractionReaction:
    message_id: UUID
    user_id: str
    code: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": str(self.message_id),
            "user_id": self.user_id,
            "code": self.code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class InteractionPin:
    id: UUID
    room_id: UUID
    message_id: UUID
    pinned_by_user_id: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "message_id": str(self.message_id),
            "pinned_by_user_id": self.pinned_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class InteractionMessage:
    id: UUID
    room_id: UUID
    message_kind: str
    body_text: str
    created_at: datetime
    author_user_id: str | None = None
    parent_id: UUID | None = None
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    mentions: tuple[InteractionMention, ...] = field(default_factory=tuple)
    reactions: tuple[InteractionReaction, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "author_user_id": self.author_user_id,
            "message_kind": self.message_kind,
            "body_text": self.body_text,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "mentions": [item.to_dict() for item in self.mentions],
            "reactions": [item.to_dict() for item in self.reactions],
        }
