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


ROOM_ACCESS_SCOPE_OPEN = "open"
ROOM_ACCESS_SCOPE_MEMBERS = "members"
ROOM_ACCESS_SCOPES = (ROOM_ACCESS_SCOPE_OPEN, ROOM_ACCESS_SCOPE_MEMBERS)

LINK_ENTITY_PROCESS = "process"
LINK_ENTITY_HELPDESK_TICKET = "helpdesk_ticket"
LINK_ENTITY_TYPES = (LINK_ENTITY_PROCESS, LINK_ENTITY_HELPDESK_TICKET)

LINK_ROLE_PRIMARY = "primary"
LINK_ROLE_REFERENCE = "reference"
LINK_ROLES = (LINK_ROLE_PRIMARY, LINK_ROLE_REFERENCE)

LINK_DELETED_EXPLICIT = "explicit"
LINK_DELETED_ROOM_DELETED = "room_deleted"

PARTICIPANT_ROLE_OWNER = "owner"
PARTICIPANT_ROLE_MEMBER = "member"


@dataclass(frozen=True)
class InteractionRoomLink:
    """Typed association between a room and a business object.

    ``link_role`` is cardinality/canonical-resolution metadata, never a
    security class: every active link with an external authority restricts
    the room equally, primary or reference.
    """

    id: str
    room_id: str
    entity_type: str
    entity_key: str
    link_role: str
    created_by_user_id: str
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_cause: str | None = None

    @property
    def active(self) -> bool:
        return self.deleted_at is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "entity_type": self.entity_type,
            "entity_key": self.entity_key,
            "link_role": self.link_role,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_cause": self.deleted_cause,
        }


@dataclass(frozen=True)
class InteractionRoomParticipant:
    room_id: str
    user_id: str
    role: str
    added_by_user_id: str
    created_at: datetime | None = None
    removed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "user_id": self.user_id,
            "role": self.role,
            "added_by_user_id": self.added_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
        }


@dataclass(frozen=True)
class InteractionRoom:
    id: str
    processo_id: str | None
    processo_codigo: str
    processo_nome: str
    created_by_user_id: str
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None = None
    access_scope: str = ROOM_ACCESS_SCOPE_OPEN
    title: str | None = None
    deleted_by_user_id: str | None = None
    links: tuple[InteractionRoomLink, ...] = ()
    participants: tuple[InteractionRoomParticipant, ...] = ()
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
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "access_scope": self.access_scope,
            "title": self.title,
            "links": [item.to_dict() for item in self.links if item.active],
            "participants": [item.to_dict() for item in self.participants],
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
