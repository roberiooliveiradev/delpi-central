from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from tm_app.domain.entities.interaction_room import (
    InteractionAttachment,
    InteractionMention,
    InteractionMessage,
    InteractionReaction,
    InteractionRoom,
)
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_S = "transformometro"
_PREVIEW = 160
_MESSAGE_COLUMNS = (
    "id, room_id, author_user_id, content, created_at, parent_id, edited_at, deleted_at"
)


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
        unread_count=int(row.get("unread_count") or 0),
        mentioned=bool(row.get("mentioned")),
    )


def _message(
    row: dict[str, Any],
    *,
    mentions: tuple[InteractionMention, ...] = (),
    reactions: tuple[InteractionReaction, ...] = (),
    attachments: tuple[InteractionAttachment, ...] = (),
    pinned: bool = False,
) -> InteractionMessage:
    parent = row.get("parent_id")
    return InteractionMessage(
        id=str(row["id"]),
        room_id=str(row["room_id"]),
        author_user_id=str(row["author_user_id"]),
        content=str(row["content"]),
        created_at=row.get("created_at"),
        parent_id=str(parent) if parent else None,
        edited_at=row.get("edited_at"),
        deleted_at=row.get("deleted_at"),
        mentions=mentions,
        reactions=reactions,
        attachments=attachments,
        pinned=pinned,
    )


def _attachment(row: dict[str, Any]) -> InteractionAttachment:
    return InteractionAttachment(
        id=str(row["id"]),
        message_id=str(row["message_id"]),
        room_id=str(row["room_id"]),
        file_name=str(row["file_name"]),
        content_type=str(row["content_type"]),
        byte_size=int(row["byte_size"]),
        uploaded_by_user_id=str(row["uploaded_by_user_id"]),
        created_at=row.get("created_at"),
        stored_name=str(row.get("stored_name") or ""),
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
    WHERE room_id = r.id AND deleted_at IS NULL
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

    def list_rooms(
        self,
        *,
        viewer_user_id: str | None = None,
        inbox_filter: str = "all",
    ) -> list[InteractionRoom]:
        viewer = viewer_user_id or "00000000-0000-0000-0000-000000000000"
        rows = self.fetch_all(
            f"""SELECT base.*,
                       COALESCE(unread.qty, 0) AS unread_count,
                       COALESCE(mentioned.flag, FALSE) AS mentioned
                FROM ({_ROOM_SELECT}) base
                LEFT JOIN LATERAL (
                    SELECT COUNT(*)::int AS qty
                    FROM {_S}.tm_interaction_messages msg
                    WHERE msg.room_id = base.id
                      AND msg.deleted_at IS NULL
                      AND msg.author_user_id <> %s::uuid
                      AND msg.created_at > COALESCE(
                          (SELECT last_read_at FROM {_S}.tm_interaction_reads
                           WHERE room_id = base.id AND user_id = %s::uuid),
                          '-infinity'::timestamptz
                      )
                ) unread ON TRUE
                LEFT JOIN LATERAL (
                    SELECT TRUE AS flag
                    FROM {_S}.tm_interaction_messages msg
                    JOIN {_S}.tm_interaction_mentions mn ON mn.message_id = msg.id
                    WHERE msg.room_id = base.id
                      AND msg.deleted_at IS NULL
                      AND mn.mentioned_user_id = %s::uuid
                      AND msg.created_at > COALESCE(
                          (SELECT last_read_at FROM {_S}.tm_interaction_reads
                           WHERE room_id = base.id AND user_id = %s::uuid),
                          '-infinity'::timestamptz
                      )
                    LIMIT 1
                ) mentioned ON TRUE
                ORDER BY COALESCE(base.last_message_at, base.updated_at) DESC, base.id DESC""",
            (viewer, viewer, viewer, viewer),
        )
        rooms = [_room(row) for row in rows]
        if inbox_filter == "unread":
            return [room for room in rooms if room.unread_count > 0]
        if inbox_filter == "mentioned":
            return [room for room in rooms if room.mentioned]
        return rooms

    def list_messages(
        self,
        room_id: str,
        *,
        limit: int,
        before_id: str | None = None,
    ) -> tuple[list[InteractionMessage], bool]:
        cursor = (before_id or "").strip() or None
        if cursor:
            anchor = self.fetch_one(
                f"""SELECT created_at, id FROM {_S}.tm_interaction_messages
                    WHERE id = %s::uuid AND room_id = %s::uuid""",
                (cursor, room_id),
            )
            if anchor is None:
                raise LookupError("Mensagem âncora não encontrada.")
            rows = self.fetch_all(
                f"""SELECT * FROM (
                        SELECT {_MESSAGE_COLUMNS}
                        FROM {_S}.tm_interaction_messages
                        WHERE room_id = %s::uuid
                          AND (created_at, id) < (%s, %s::uuid)
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s
                    ) older
                    ORDER BY created_at ASC, id ASC""",
                (room_id, anchor["created_at"], str(anchor["id"]), limit + 1),
            )
        else:
            rows = self.fetch_all(
                f"""SELECT * FROM (
                        SELECT {_MESSAGE_COLUMNS}
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
        return self._decorate([_message(row) for row in visible]), has_more

    def add_message(
        self,
        *,
        room_id: str,
        author_user_id: str,
        content: str,
        parent_id: str | None = None,
        mentions: tuple[tuple[str, str], ...] = (),
    ) -> InteractionMessage:
        if parent_id:
            row = self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_messages
                        (room_id, author_user_id, content, parent_id)
                    VALUES (%s::uuid, %s::uuid, %s, %s::uuid)
                    RETURNING {_MESSAGE_COLUMNS}""",
                (room_id, author_user_id, content, parent_id),
            )
        else:
            row = self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_messages
                        (room_id, author_user_id, content)
                    VALUES (%s::uuid, %s::uuid, %s)
                    RETURNING {_MESSAGE_COLUMNS}""",
                (room_id, author_user_id, content),
            )
        if row is None:
            raise RuntimeError("Falha ao gravar a mensagem.")
        message_id = str(row["id"])
        for user_id, label in mentions:
            self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_mentions (message_id, mentioned_user_id, label)
                    VALUES (%s::uuid, %s::uuid, %s)
                    ON CONFLICT (message_id, mentioned_user_id) DO UPDATE SET label = EXCLUDED.label
                    RETURNING message_id""",
                (message_id, user_id, label),
            )
        self.execute_returning_one(
            f"UPDATE {_S}.tm_interaction_rooms SET updated_at = NOW() WHERE id = %s::uuid RETURNING id",
            (room_id,),
        )
        return self.get_message(message_id) or _message(row)

    def get_message(self, message_id: str) -> InteractionMessage | None:
        row = self.fetch_one(
            f"""SELECT {_MESSAGE_COLUMNS}
                FROM {_S}.tm_interaction_messages WHERE id = %s::uuid""",
            (message_id,),
        )
        if row is None:
            return None
        return self._decorate([_message(row)])[0]

    def update_message(self, *, message_id: str, content: str) -> InteractionMessage | None:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_interaction_messages
                SET content = %s, edited_at = NOW()
                WHERE id = %s::uuid AND deleted_at IS NULL
                RETURNING id""",
            (content, message_id),
        )
        if row is None:
            return None
        return self.get_message(message_id)

    def soft_delete_message(self, message_id: str) -> InteractionMessage | None:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_interaction_messages
                SET deleted_at = NOW()
                WHERE id = %s::uuid AND deleted_at IS NULL
                RETURNING id""",
            (message_id,),
        )
        if row is None:
            return None
        return self.get_message(message_id)

    def toggle_reaction(self, *, message_id: str, user_id: str, code: str) -> None:
        removed = self.execute_returning_one(
            f"""DELETE FROM {_S}.tm_interaction_reactions
                WHERE message_id = %s::uuid AND user_id = %s::uuid AND code = %s
                RETURNING code""",
            (message_id, user_id, code),
        )
        if removed is not None:
            return
        self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_reactions (message_id, user_id, code)
                VALUES (%s::uuid, %s::uuid, %s)
                RETURNING code""",
            (message_id, user_id, code),
        )

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None:
        self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_pins (room_id, message_id, pinned_by_user_id)
                VALUES (%s::uuid, %s::uuid, %s::uuid)
                ON CONFLICT (room_id, message_id) DO NOTHING
                RETURNING id""",
            (room_id, message_id, user_id),
        )

    def unpin_message(self, *, room_id: str, message_id: str) -> None:
        self.execute(
            f"""DELETE FROM {_S}.tm_interaction_pins
                WHERE room_id = %s::uuid AND message_id = %s::uuid""",
            (room_id, message_id),
        )

    def mark_read(self, *, room_id: str, user_id: str) -> None:
        self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_reads (room_id, user_id, last_read_at)
                VALUES (%s::uuid, %s::uuid, NOW())
                ON CONFLICT (room_id, user_id) DO UPDATE SET last_read_at = NOW()
                RETURNING room_id""",
            (room_id, user_id),
        )

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_attachments
                    (id, message_id, room_id, file_name, stored_name, content_type, byte_size, uploaded_by_user_id)
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s::uuid)
                RETURNING id, message_id, room_id, file_name, stored_name, content_type, byte_size,
                          uploaded_by_user_id, created_at""",
            (
                attachment.id,
                attachment.message_id,
                attachment.room_id,
                attachment.file_name,
                attachment.stored_name,
                attachment.content_type,
                attachment.byte_size,
                attachment.uploaded_by_user_id,
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao gravar o anexo.")
        return _attachment(row)

    def get_attachment(self, attachment_id: str) -> InteractionAttachment | None:
        row = self.fetch_one(
            f"""SELECT id, message_id, room_id, file_name, stored_name, content_type, byte_size,
                       uploaded_by_user_id, created_at
                FROM {_S}.tm_interaction_attachments WHERE id = %s::uuid""",
            (attachment_id,),
        )
        return _attachment(row) if row else None

    def delete_attachment(self, attachment_id: str) -> InteractionAttachment | None:
        row = self.execute_returning_one(
            f"""DELETE FROM {_S}.tm_interaction_attachments
                WHERE id = %s::uuid
                RETURNING id, message_id, room_id, file_name, stored_name, content_type, byte_size,
                          uploaded_by_user_id, created_at""",
            (attachment_id,),
        )
        return _attachment(row) if row else None

    def list_attachments(self, room_id: str) -> list[InteractionAttachment]:
        rows = self.fetch_all(
            f"""SELECT id, message_id, room_id, file_name, stored_name, content_type, byte_size,
                       uploaded_by_user_id, created_at
                FROM {_S}.tm_interaction_attachments
                WHERE room_id = %s::uuid
                ORDER BY created_at DESC, id DESC""",
            (room_id,),
        )
        return [_attachment(row) for row in rows]

    def _decorate(self, messages: list[InteractionMessage]) -> list[InteractionMessage]:
        if not messages:
            return []
        ids = [item.id for item in messages]
        mention_rows = self.fetch_all(
            f"""SELECT message_id, mentioned_user_id, label
                FROM {_S}.tm_interaction_mentions
                WHERE message_id = ANY(%s::uuid[])""",
            (ids,),
        )
        reaction_rows = self.fetch_all(
            f"""SELECT message_id, user_id, code
                FROM {_S}.tm_interaction_reactions
                WHERE message_id = ANY(%s::uuid[])""",
            (ids,),
        )
        attachment_rows = self.fetch_all(
            f"""SELECT id, message_id, room_id, file_name, stored_name, content_type, byte_size,
                       uploaded_by_user_id, created_at
                FROM {_S}.tm_interaction_attachments
                WHERE message_id = ANY(%s::uuid[])
                ORDER BY created_at ASC, id ASC""",
            (ids,),
        )
        pin_rows = self.fetch_all(
            f"""SELECT message_id FROM {_S}.tm_interaction_pins
                WHERE message_id = ANY(%s::uuid[])""",
            (ids,),
        )
        mentions: dict[str, list[InteractionMention]] = defaultdict(list)
        reactions: dict[str, list[InteractionReaction]] = defaultdict(list)
        attachments: dict[str, list[InteractionAttachment]] = defaultdict(list)
        for row in mention_rows:
            mentions[str(row["message_id"])].append(
                InteractionMention(user_id=str(row["mentioned_user_id"]), label=str(row["label"]))
            )
        for row in reaction_rows:
            reactions[str(row["message_id"])].append(
                InteractionReaction(user_id=str(row["user_id"]), code=str(row["code"]))
            )
        for row in attachment_rows:
            attachments[str(row["message_id"])].append(_attachment(row))
        pinned = {str(row["message_id"]) for row in pin_rows}
        return [
            replace(
                item,
                mentions=tuple(mentions.get(item.id, ())),
                reactions=tuple(reactions.get(item.id, ())),
                attachments=tuple(attachments.get(item.id, ())),
                pinned=item.id in pinned,
            )
            for item in messages
        ]


class InMemoryInteractionRoomRepository(InteractionRoomRepositoryPort):
    def __init__(self) -> None:
        self.processes: set[str] = set()
        self.rooms: dict[str, InteractionRoom] = {}
        self.by_process: dict[str, str] = {}
        self.messages: dict[str, InteractionMessage] = {}
        self.attachments: dict[str, InteractionAttachment] = {}
        self.pins: set[tuple[str, str]] = set()
        self.reads: dict[tuple[str, str], datetime] = {}

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

    def list_rooms(
        self,
        *,
        viewer_user_id: str | None = None,
        inbox_filter: str = "all",
    ) -> list[InteractionRoom]:
        rooms = sorted(self.rooms.values(), key=lambda room: room.updated_at or datetime.min, reverse=True)
        visible: list[InteractionRoom] = []
        for room in rooms:
            unread, mentioned = self._signals(room.id, viewer_user_id)
            shown = replace(room, unread_count=unread, mentioned=mentioned)
            if inbox_filter == "unread" and unread <= 0:
                continue
            if inbox_filter == "mentioned" and not mentioned:
                continue
            visible.append(shown)
        return visible

    def list_messages(
        self,
        room_id: str,
        *,
        limit: int,
        before_id: str | None = None,
    ) -> tuple[list[InteractionMessage], bool]:
        rows = [self._view(item) for item in self.messages.values() if item.room_id == room_id]
        rows.sort(key=lambda item: (item.created_at or datetime.min, item.id))
        cursor = (before_id or "").strip() or None
        if cursor:
            anchor = next((item for item in rows if item.id == cursor), None)
            if anchor is None:
                raise LookupError("Mensagem âncora não encontrada.")
            anchor_key = (anchor.created_at or datetime.min, anchor.id)
            rows = [
                item
                for item in rows
                if (item.created_at or datetime.min, item.id) < anchor_key
            ]
        has_more = len(rows) > limit
        return (rows[-limit:] if has_more else rows), has_more

    def add_message(
        self,
        *,
        room_id: str,
        author_user_id: str,
        content: str,
        parent_id: str | None = None,
        mentions: tuple[tuple[str, str], ...] = (),
    ) -> InteractionMessage:
        now = datetime.now(timezone.utc)
        message = InteractionMessage(
            id=str(uuid4()),
            room_id=room_id,
            author_user_id=author_user_id,
            content=content,
            created_at=now,
            parent_id=parent_id,
            mentions=tuple(InteractionMention(user_id=user_id, label=label) for user_id, label in mentions),
        )
        self.messages[message.id] = message
        self._refresh_preview(room_id)
        return self._view(message)

    def get_message(self, message_id: str) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        return self._view(message) if message else None

    def update_message(self, *, message_id: str, content: str) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.deleted_at is not None:
            return None
        self.messages[message_id] = replace(message, content=content, edited_at=datetime.now(timezone.utc))
        self._refresh_preview(message.room_id)
        return self._view(self.messages[message_id])

    def soft_delete_message(self, message_id: str) -> InteractionMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.deleted_at is not None:
            return None
        self.messages[message_id] = replace(message, deleted_at=datetime.now(timezone.utc))
        self._refresh_preview(message.room_id)
        return self._view(self.messages[message_id])

    def toggle_reaction(self, *, message_id: str, user_id: str, code: str) -> None:
        message = self.messages[message_id]
        current = list(message.reactions)
        kept = [item for item in current if not (item.user_id == user_id and item.code == code)]
        if len(kept) == len(current):
            kept.append(InteractionReaction(user_id=user_id, code=code))
        self.messages[message_id] = replace(message, reactions=tuple(kept))

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None:
        del user_id
        self.pins.add((room_id, message_id))

    def unpin_message(self, *, room_id: str, message_id: str) -> None:
        self.pins.discard((room_id, message_id))

    def mark_read(self, *, room_id: str, user_id: str) -> None:
        self.reads[(room_id, user_id)] = datetime.now(timezone.utc)

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment:
        stored = replace(
            attachment,
            id=attachment.id or str(uuid4()),
            created_at=attachment.created_at or datetime.now(timezone.utc),
        )
        self.attachments[stored.id] = stored
        return stored

    def get_attachment(self, attachment_id: str) -> InteractionAttachment | None:
        return self.attachments.get(attachment_id)

    def delete_attachment(self, attachment_id: str) -> InteractionAttachment | None:
        return self.attachments.pop(attachment_id, None)

    def list_attachments(self, room_id: str) -> list[InteractionAttachment]:
        rows = [item for item in self.attachments.values() if item.room_id == room_id]
        rows.sort(key=lambda item: item.created_at or datetime.min, reverse=True)
        return rows

    def _view(self, message: InteractionMessage) -> InteractionMessage:
        files = tuple(
            item for item in self.attachments.values() if item.message_id == message.id
        )
        return replace(message, attachments=files, pinned=(message.room_id, message.id) in self.pins)

    def _refresh_preview(self, room_id: str) -> None:
        room = self.rooms.get(room_id)
        if room is None:
            return
        rows = [
            item
            for item in self.messages.values()
            if item.room_id == room_id and item.deleted_at is None
        ]
        rows.sort(key=lambda item: (item.created_at or datetime.min, item.id))
        last = rows[-1] if rows else None
        self.rooms[room_id] = replace(
            room,
            last_message_preview=_preview(last.content) if last else None,
            last_message_at=last.created_at if last else None,
            updated_at=datetime.now(timezone.utc),
        )

    def _signals(self, room_id: str, viewer_user_id: str | None) -> tuple[int, bool]:
        if not viewer_user_id:
            return 0, False
        last_read = self.reads.get((room_id, viewer_user_id))
        unread = 0
        mentioned = False
        for message in self.messages.values():
            if message.room_id != room_id or message.deleted_at is not None:
                continue
            created = message.created_at
            if last_read is not None and created is not None and created <= last_read:
                continue
            if message.author_user_id != viewer_user_id:
                unread += 1
            if any(item.user_id == viewer_user_id for item in message.mentions):
                mentioned = True
        return unread, mentioned
