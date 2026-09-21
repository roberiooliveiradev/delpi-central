from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InteractionMention:
    user_id: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return {"user_id": self.user_id, "label": self.label}


@dataclass(frozen=True)
class InteractionReaction:
    user_id: str
    code: str

    def to_dict(self) -> dict[str, Any]:
        return {"user_id": self.user_id, "code": self.code}


@dataclass(frozen=True)
class InteractionAttachment:
    id: str
    message_id: str
    room_id: str
    file_name: str
    content_type: str
    byte_size: int
    uploaded_by_user_id: str
    created_at: datetime | None
    stored_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "room_id": self.room_id,
            "file_name": self.file_name,
            "content_type": self.content_type,
            "byte_size": self.byte_size,
            "uploaded_by_user_id": self.uploaded_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class InteractionRoom:
    id: str
    processo_id: str
    processo_codigo: str
    processo_nome: str
    created_by_user_id: str
    created_at: datetime | None
    updated_at: datetime | None
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    mentioned: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "processo_id": self.processo_id,
            "processo_codigo": self.processo_codigo,
            "processo_nome": self.processo_nome,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_preview": self.last_message_preview,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "unread_count": self.unread_count,
            "mentioned": self.mentioned,
        }


@dataclass(frozen=True)
class InteractionMessage:
    id: str
    room_id: str
    author_user_id: str
    content: str
    created_at: datetime | None
    parent_id: str | None = None
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    mentions: tuple[InteractionMention, ...] = ()
    reactions: tuple[InteractionReaction, ...] = ()
    attachments: tuple[InteractionAttachment, ...] = ()
    pinned: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "author_user_id": self.author_user_id,
            "content": "" if self.deleted_at else self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "parent_id": self.parent_id,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "mentions": [item.to_dict() for item in self.mentions],
            "reactions": [item.to_dict() for item in self.reactions],
            "attachments": [item.to_dict() for item in self.attachments],
            "pinned": self.pinned,
        }
