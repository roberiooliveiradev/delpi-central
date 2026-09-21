from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


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
        }


@dataclass(frozen=True)
class InteractionMessage:
    id: str
    room_id: str
    author_user_id: str
    content: str
    created_at: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "author_user_id": self.author_user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
