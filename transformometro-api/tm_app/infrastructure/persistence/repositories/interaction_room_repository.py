from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from tm_app.domain.entities.interaction_room import InteractionMessage, InteractionRoom
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_S = "transformometro"
_PREVIEW = 160


def _preview(content: str | None) -> str | None:
    if not content:
        return None
    text = " ".join(content.split())
    if len(text) <= _PREVIEW:
        return text
    return text[: _PREVIEW - 1].rstrip() + "…"


def _room(row: dict[str, Any]) -> InteractionRoom:
    return InteractionRoom(
        id=str(row["id"]),
        processo_id=str(row["processo_id"]),
        processo_codigo=str(row.get("codigo_processo") or ""),
        processo_nome=str(row.get("nome_processo") or ""),
        created_by_user_id=str(row["created_by_user_id"]),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        last_message_preview=_preview(row.get("last_content")),
        last_message_at=row.get("last_message_at"),
    )


def _message(row: dict[str, Any]) -> InteractionMessage:
    return InteractionMessage(
        id=str(row["id"]),
        room_id=str(row["room_id"]),
        author_user_id=str(row["author_user_id"]),
        content=str(row["content"]),
        created_at=row.get("created_at"),
    )


_ROOM_SELECT = f"""
SELECT r.id, r.processo_id, r.created_by_user_id, r.created_at, r.updated_at,
       p.codigo_processo, p.nome_processo,
       m.content AS last_content, m.created_at AS last_message_at
FROM {_S}.tm_interaction_rooms r
JOIN {_S}.processos p ON p.processo_id = r.processo_id AND p.deletado = FALSE
LEFT JOIN LATERAL (
    SELECT content, created_at
    FROM {_S}.tm_interaction_messages
    WHERE room_id = r.id
    ORDER BY created_at DESC, id DESC
    LIMIT 1
) m ON TRUE
"""


class InteractionRoomRepository(PluginBaseRepository, InteractionRoomRepositoryPort):
    def get_or_create(self, *, processo_id: str, created_by_user_id: str) -> InteractionRoom | None:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_rooms AS room (processo_id, created_by_user_id)
                SELECT %s::uuid, %s::uuid
                WHERE EXISTS (
                    SELECT 1 FROM {_S}.processos
                    WHERE processo_id = %s::uuid AND deletado = FALSE
                )
                ON CONFLICT (processo_id) DO UPDATE
                    SET updated_at = room.updated_at
                RETURNING id""",
            (processo_id, created_by_user_id, processo_id),
        )
        if row is None:
            return None
        return self.get(str(row["id"]))

    def get(self, room_id: str) -> InteractionRoom | None:
        row = self.fetch_one(f"{_ROOM_SELECT} WHERE r.id = %s::uuid", (room_id,))
        return _room(row) if row else None

    def list_rooms(self) -> list[InteractionRoom]:
        rows = self.fetch_all(
            f"{_ROOM_SELECT} ORDER BY COALESCE(m.created_at, r.updated_at) DESC, r.id DESC"
        )
        return [_room(row) for row in rows]

    def list_messages(self, room_id: str, *, limit: int) -> tuple[list[InteractionMessage], bool]:
        rows = self.fetch_all(
            f"""SELECT * FROM (
                    SELECT id, room_id, author_user_id, content, created_at
                    FROM {_S}.tm_interaction_messages
                    WHERE room_id = %s::uuid
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                ) recent
                ORDER BY created_at ASC, id ASC""",
            (room_id, limit + 1),
        )
        has_more = len(rows) > limit
        visible = rows[-limit:] if has_more else rows
        return [_message(row) for row in visible], has_more

    def add_message(self, *, room_id: str, author_user_id: str, content: str) -> InteractionMessage:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_messages (room_id, author_user_id, content)
                VALUES (%s::uuid, %s::uuid, %s)
                RETURNING id, room_id, author_user_id, content, created_at""",
            (room_id, author_user_id, content),
        )
        if row is None:
            raise RuntimeError("Falha ao gravar a mensagem.")
        self.execute_returning_one(
            f"UPDATE {_S}.tm_interaction_rooms SET updated_at = NOW() WHERE id = %s::uuid RETURNING id",
            (room_id,),
        )
        return _message(row)

    def get_message(self, message_id: str) -> InteractionMessage | None:
        row = self.fetch_one(
            f"""SELECT id, room_id, author_user_id, content, created_at
                FROM {_S}.tm_interaction_messages WHERE id = %s::uuid""",
            (message_id,),
        )
        return _message(row) if row else None


class InMemoryInteractionRoomRepository(InteractionRoomRepositoryPort):
    def __init__(self) -> None:
        self.processes: set[str] = set()
        self.rooms: dict[str, InteractionRoom] = {}
        self.by_process: dict[str, str] = {}
        self.messages: dict[str, InteractionMessage] = {}

    def get_or_create(self, *, processo_id: str, created_by_user_id: str) -> InteractionRoom | None:
        if processo_id not in self.processes:
            return None
        existing = self.by_process.get(processo_id)
        if existing:
            return self.rooms[existing]
        now = datetime.now(timezone.utc)
        room = InteractionRoom(
            id=str(uuid4()),
            processo_id=processo_id,
            processo_codigo="PROC",
            processo_nome="Processo",
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
        )
        self.rooms[room.id] = room
        self.by_process[processo_id] = room.id
        return room

    def get(self, room_id: str) -> InteractionRoom | None:
        return self.rooms.get(room_id)

    def list_rooms(self) -> list[InteractionRoom]:
        return sorted(self.rooms.values(), key=lambda room: room.updated_at or datetime.min, reverse=True)

    def list_messages(self, room_id: str, *, limit: int) -> tuple[list[InteractionMessage], bool]:
        rows = [item for item in self.messages.values() if item.room_id == room_id]
        rows.sort(key=lambda item: (item.created_at or datetime.min, item.id))
        has_more = len(rows) > limit
        return rows[-limit:], has_more

    def add_message(self, *, room_id: str, author_user_id: str, content: str) -> InteractionMessage:
        message = InteractionMessage(
            id=str(uuid4()),
            room_id=room_id,
            author_user_id=author_user_id,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.messages[message.id] = message
        return message

    def get_message(self, message_id: str) -> InteractionMessage | None:
        return self.messages.get(message_id)
