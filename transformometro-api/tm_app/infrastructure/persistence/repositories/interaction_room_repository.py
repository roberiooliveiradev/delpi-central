from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import threading
from typing import Any
from uuid import uuid4

from tm_app.domain.entities.interaction_room import (
    LINK_DELETED_ROOM_DELETED,
    InteractionAttachment,
    InteractionMention,
    InteractionMessage,
    InteractionReaction,
    InteractionRoom,
    InteractionRoomLink,
    InteractionRoomParticipant,
)
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.domain.services.interaction_room_access_service import (
    PrimaryLinkConflict,
    RoomAccessExpansionBlocked,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

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


def _room(
    row: dict[str, Any],
    *,
    links: tuple[InteractionRoomLink, ...] = (),
    participants: tuple[InteractionRoomParticipant, ...] = (),
) -> InteractionRoom:
    processo_id = row.get("processo_id")
    return InteractionRoom(
        id=str(row["id"]),
        processo_id=str(processo_id) if processo_id else None,
        processo_codigo=str(row.get("codigo_processo") or ""),
        processo_nome=str(row.get("nome_processo") or ""),
        created_by_user_id=str(row["created_by_user_id"]),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        deleted_at=row.get("deleted_at"),
        access_scope=str(row.get("access_scope") or "open"),
        title=str(row.get("title") or "") or None,
        deleted_by_user_id=(
            str(row["deleted_by_user_id"]) if row.get("deleted_by_user_id") else None
        ),
        links=links,
        participants=participants,
        last_message_preview=_preview(row.get("last_content")),
        last_message_at=row.get("last_message_at"),
        unread_count=int(row.get("unread_count") or 0),
        mentioned=bool(row.get("mentioned")),
    )


def _link(row: dict[str, Any]) -> InteractionRoomLink:
    return InteractionRoomLink(
        id=str(row["id"]),
        room_id=str(row["room_id"]),
        entity_type=str(row["entity_type"]),
        entity_key=str(row["entity_key"]),
        link_role=str(row["link_role"]),
        created_by_user_id=str(row["created_by_user_id"]),
        created_at=row.get("created_at"),
        deleted_at=row.get("deleted_at"),
        deleted_cause=row.get("deleted_cause"),
    )


def _participant(row: dict[str, Any]) -> InteractionRoomParticipant:
    return InteractionRoomParticipant(
        room_id=str(row["room_id"]),
        user_id=str(row["user_id"]),
        role=str(row["role"]),
        added_by_user_id=str(row["added_by_user_id"]),
        created_at=row.get("created_at"),
        removed_at=row.get("removed_at"),
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
       r.deleted_at, r.access_scope, r.title, r.deleted_by_user_id,
       p.codigo_processo, p.nome_processo,
       m.content AS last_content, m.created_at AS last_message_at
FROM {_S}.tm_interaction_rooms r
LEFT JOIN {_S}.processos p ON p.processo_id = r.processo_id AND p.deletado = FALSE
LEFT JOIN LATERAL (
    SELECT content, created_at
    FROM {_S}.tm_interaction_messages
    WHERE room_id = r.id AND deleted_at IS NULL
    ORDER BY created_at DESC, id DESC
    LIMIT 1
) m ON TRUE
"""


class InteractionRoomRepository(PluginBaseRepository, InteractionRoomRepositoryPort):
    def get_by_process(self, processo_id: str) -> InteractionRoom | None:
        """Read-only locate by the legacy ``processo_id`` column."""
        row = self.fetch_one(
            f"{_ROOM_SELECT} WHERE r.processo_id = %s::uuid AND r.deleted_at IS NULL",
            (processo_id,),
        )
        return self._with_graph(_room(row)) if row else None

    def create_room_graph(
        self,
        *,
        title: str | None,
        access_scope: str,
        created_by_user_id: str,
        processo_id: str | None = None,
        links: tuple[tuple[str, str, str], ...] = (),
        owner_participant: bool = False,
        participant_ids: tuple[str, ...] = (),
    ) -> InteractionRoom | None:
        """One transaction: room + links + participants. Any failure —
        including a competing primary claim (23505) — rolls back the whole
        graph; no orphan rows."""
        room_id: str | None = None
        try:
            with self.db() as connection:
                if processo_id is None:
                    row = self.execute_returning_one(
                        f"""INSERT INTO {_S}.tm_interaction_rooms
                                (title, access_scope, created_by_user_id)
                            VALUES (%s, %s, %s::uuid)
                            RETURNING id""",
                        (title, access_scope, created_by_user_id),
                        auto_commit=False,
                    )
                else:
                    row = self.execute_returning_one(
                        f"""INSERT INTO {_S}.tm_interaction_rooms
                                (processo_id, title, access_scope, created_by_user_id)
                            SELECT %s::uuid, %s, %s, %s::uuid
                            WHERE EXISTS (
                                SELECT 1 FROM {_S}.processos
                                WHERE processo_id = %s::uuid AND deletado = FALSE
                            )
                            RETURNING id""",
                        (processo_id, title, access_scope, created_by_user_id, processo_id),
                        auto_commit=False,
                    )
                if row is None:
                    return None
                room_id = str(row["id"])
                for entity_type, entity_key, link_role in links:
                    self.execute(
                        f"""INSERT INTO {_S}.tm_interaction_room_links
                                (room_id, entity_type, entity_key, link_role, created_by_user_id)
                            VALUES (%s::uuid, %s, %s, %s, %s::uuid)""",
                        (room_id, entity_type, entity_key, link_role, created_by_user_id),
                        auto_commit=False,
                    )
                member_ids = list(participant_ids)
                if owner_participant:
                    member_ids.insert(0, created_by_user_id)
                for member_id in dict.fromkeys(member_ids):
                    self.execute(
                        f"""INSERT INTO {_S}.tm_interaction_room_participants
                                (room_id, user_id, role, added_by_user_id)
                            VALUES (%s::uuid, %s::uuid, %s, %s::uuid)
                            ON CONFLICT (room_id, user_id) DO NOTHING""",
                        (
                            room_id,
                            member_id,
                            "owner" if member_id == created_by_user_id else "member",
                            created_by_user_id,
                        ),
                        auto_commit=False,
                    )
                connection.commit()
        except PluginsRepositoryError as exc:
            if self._is_primary_conflict(exc):
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                ) from exc
            raise
        return self.get(room_id)

    def get(self, room_id: str) -> InteractionRoom | None:
        """Active room only — soft-deleted rooms are invisible to reads."""
        row = self.fetch_one(
            f"{_ROOM_SELECT} WHERE r.id = %s::uuid AND r.deleted_at IS NULL",
            (room_id,),
        )
        if row is None:
            return None
        return self._with_graph(_room(row))

    def get_raw(self, room_id: str) -> InteractionRoom | None:
        row = self.fetch_one(f"{_ROOM_SELECT} WHERE r.id = %s::uuid", (room_id,))
        if row is None:
            return None
        return _room(
            row,
            links=tuple(self.list_links(room_id, include_inactive=True)),
            participants=tuple(self.list_participants(room_id, active_only=False)),
        )

    def _with_graph(self, room: InteractionRoom) -> InteractionRoom:
        """Attach active links + current participants — every content read
        re-evaluates authorization against the fresh link set."""
        return replace(
            room,
            links=tuple(self.list_links(room.id)),
            participants=tuple(self.list_participants(room.id)),
        )

    def soft_delete(
        self, room_id: str, *, actor_user_id: str | None = None
    ) -> InteractionRoom | None:
        """Atomic: room tombstone + link inactivation ('room_deleted') in a
        single transaction. Releases every active primary claim without
        touching history."""
        with self.db() as connection:
            row = self.execute_returning_one(
                f"""UPDATE {_S}.tm_interaction_rooms
                    SET deleted_at = NOW(), deleted_by_user_id = %s::uuid,
                        updated_at = NOW()
                    WHERE id = %s::uuid AND deleted_at IS NULL
                    RETURNING id""",
                (actor_user_id, room_id),
                auto_commit=False,
            )
            if row is None:
                return None
            self.execute(
                f"""UPDATE {_S}.tm_interaction_room_links
                    SET deleted_at = NOW(), deleted_cause = '{LINK_DELETED_ROOM_DELETED}'
                    WHERE room_id = %s::uuid AND deleted_at IS NULL""",
                (room_id,),
                auto_commit=False,
            )
            connection.commit()
        return self.get_raw(room_id)

    def restore_room(self, room_id: str) -> InteractionRoom | None:
        """Atomic restore: clears the room tombstone and revives only links
        inactivated by the room deletion — never explicit removals. A
        competing active primary claim aborts the whole transaction
        (no partial reactivation)."""
        try:
            with self.db() as connection:
                row = self.execute_returning_one(
                    f"""UPDATE {_S}.tm_interaction_rooms
                        SET deleted_at = NULL, deleted_by_user_id = NULL,
                            updated_at = NOW()
                        WHERE id = %s::uuid AND deleted_at IS NOT NULL
                        RETURNING id""",
                    (room_id,),
                    auto_commit=False,
                )
                if row is None:
                    return None
                self.execute(
                    f"""UPDATE {_S}.tm_interaction_room_links
                        SET deleted_at = NULL, deleted_cause = NULL
                        WHERE room_id = %s::uuid
                          AND deleted_cause = '{LINK_DELETED_ROOM_DELETED}'""",
                    (room_id,),
                    auto_commit=False,
                )
                connection.commit()
        except PluginsRepositoryError as exc:
            if self._is_primary_conflict(exc):
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                ) from exc
            raise
        return self.get_raw(room_id)

    # --- typed links --------------------------------------------------------

    def list_links(
        self, room_id: str, *, include_inactive: bool = False
    ) -> list[InteractionRoomLink]:
        inactive = "" if include_inactive else "AND deleted_at IS NULL"
        rows = self.fetch_all(
            f"""SELECT id, room_id, entity_type, entity_key, link_role,
                       created_by_user_id, created_at, deleted_at, deleted_cause
                FROM {_S}.tm_interaction_room_links
                WHERE room_id = %s::uuid {inactive}
                ORDER BY created_at ASC, id ASC""",
            (room_id,),
        )
        return [_link(row) for row in rows]

    def find_active_primary_room(
        self, entity_type: str, entity_key: str
    ) -> InteractionRoom | None:
        row = self.fetch_one(
            f"""{_ROOM_SELECT}
                JOIN {_S}.tm_interaction_room_links l ON l.room_id = r.id
                WHERE l.entity_type = %s AND l.entity_key = %s
                  AND l.link_role = 'primary' AND l.deleted_at IS NULL
                  AND r.deleted_at IS NULL""",
            (entity_type, entity_key),
        )
        return self._with_graph(_room(row)) if row else None

    def upsert_link(
        self,
        *,
        room_id: str,
        entity_type: str,
        entity_key: str,
        link_role: str,
        actor_user_id: str,
    ) -> InteractionRoomLink:
        try:
            row = self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_room_links
                        (room_id, entity_type, entity_key, link_role, created_by_user_id)
                    VALUES (%s::uuid, %s, %s, %s, %s::uuid)
                    ON CONFLICT (room_id, entity_type, entity_key) DO UPDATE SET
                        link_role = EXCLUDED.link_role,
                        deleted_at = NULL,
                        deleted_cause = NULL
                    RETURNING id""",
                (room_id, entity_type, entity_key, link_role, actor_user_id),
            )
        except PluginsRepositoryError as exc:
            if self._is_primary_conflict(exc):
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                ) from exc
            raise
        if row is None:
            raise RuntimeError("Falha ao gravar o vínculo.")
        return self._link_by_id(str(row["id"])) or InteractionRoomLink(
            id=str(row["id"]),
            room_id=room_id,
            entity_type=entity_type,
            entity_key=entity_key,
            link_role=link_role,
            created_by_user_id=actor_user_id,
        )

    def _link_by_id(self, link_id: str) -> InteractionRoomLink | None:
        row = self.fetch_one(
            f"""SELECT id, room_id, entity_type, entity_key, link_role,
                       created_by_user_id, created_at, deleted_at, deleted_cause
                FROM {_S}.tm_interaction_room_links WHERE id = %s::uuid""",
            (link_id,),
        )
        return _link(row) if row else None

    def tombstone_link(self, link_id: str, *, cause: str) -> InteractionRoomLink | None:
        row = self.execute_returning_one(
            f"""UPDATE {_S}.tm_interaction_room_links
                SET deleted_at = NOW(), deleted_cause = %s
                WHERE id = %s::uuid AND deleted_at IS NULL
                RETURNING id""",
            (cause, link_id),
        )
        return self._link_by_id(str(row["id"])) if row else None

    @staticmethod
    def _lock_room(connection, room_id: str) -> None:
        """Serialize history writers against restrictive-link removal
        (R-1 TOCTOU fix): every protected-artifact write and the guarded
        tombstone take this single-row lock first — consistent ordering,
        no second row ever locked → no deadlock."""
        connection.execute(
            f"SELECT id FROM {_S}.tm_interaction_rooms WHERE id = %s::uuid FOR UPDATE",
            (room_id,),
        )

    def tombstone_link_guarded(
        self, *, room_id: str, link_id: str, cause: str
    ) -> InteractionRoomLink | None:
        """Lock → recount → tombstone in ONE transaction (see port)."""
        with self.db() as connection:
            self._lock_room(connection, room_id)
            row = connection.execute(
                f"""SELECT (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_messages
                        WHERE room_id = %s::uuid
                    ) + (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_attachments
                        WHERE room_id = %s::uuid
                    ) + (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_mentions mn
                        JOIN {_S}.tm_interaction_messages m ON m.id = mn.message_id
                        WHERE m.room_id = %s::uuid
                    ) + (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_reactions rc
                        JOIN {_S}.tm_interaction_messages m ON m.id = rc.message_id
                        WHERE m.room_id = %s::uuid
                    ) + (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_pins
                        WHERE room_id = %s::uuid
                    ) + (
                        SELECT COUNT(*) FROM {_S}.tm_interaction_reads
                        WHERE room_id = %s::uuid
                    ) AS total""",
                (room_id,) * 6,
            ).fetchone()
            if row is not None and int(dict(row)["total"] or 0) > 0:
                raise RoomAccessExpansionBlocked(
                    "A remoção ampliaria o acesso ao histórico protegido."
                )
            tomb = connection.execute(
                f"""UPDATE {_S}.tm_interaction_room_links
                    SET deleted_at = NOW(), deleted_cause = %s
                    WHERE id = %s::uuid AND room_id = %s::uuid
                      AND deleted_at IS NULL
                    RETURNING id""",
                (cause, link_id, room_id),
            ).fetchone()
            connection.commit()
        return self._link_by_id(str(dict(tomb)["id"])) if tomb else None

    # --- participants -------------------------------------------------------

    def is_participant(self, room_id: str, user_id: str) -> bool:
        row = self.fetch_one(
            f"""SELECT room_id FROM {_S}.tm_interaction_room_participants
                WHERE room_id = %s::uuid AND user_id = %s::uuid
                  AND removed_at IS NULL""",
            (room_id, user_id),
        )
        return row is not None

    def add_participant(
        self, *, room_id: str, user_id: str, role: str, actor_user_id: str
    ) -> InteractionRoomParticipant:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_interaction_room_participants
                    (room_id, user_id, role, added_by_user_id)
                VALUES (%s::uuid, %s::uuid, %s, %s::uuid)
                ON CONFLICT (room_id, user_id) DO UPDATE SET
                    role = EXCLUDED.role,
                    removed_at = NULL,
                    added_by_user_id = EXCLUDED.added_by_user_id
                RETURNING room_id, user_id, role, added_by_user_id,
                          created_at, removed_at""",
            (room_id, user_id, role, actor_user_id),
        )
        if row is None:
            raise RuntimeError("Falha ao gravar o participante.")
        return _participant(row)

    def remove_participant(self, *, room_id: str, user_id: str) -> None:
        self.execute(
            f"""UPDATE {_S}.tm_interaction_room_participants
                SET removed_at = NOW()
                WHERE room_id = %s::uuid AND user_id = %s::uuid
                  AND removed_at IS NULL""",
            (room_id, user_id),
        )

    def list_participants(
        self, room_id: str, *, active_only: bool = True
    ) -> list[InteractionRoomParticipant]:
        active = "AND removed_at IS NULL" if active_only else ""
        rows = self.fetch_all(
            f"""SELECT room_id, user_id, role, added_by_user_id,
                       created_at, removed_at
                FROM {_S}.tm_interaction_room_participants
                WHERE room_id = %s::uuid {active}
                ORDER BY created_at ASC, user_id ASC""",
            (room_id,),
        )
        return [_participant(row) for row in rows]

    # --- authorization support ----------------------------------------------

    def protected_content_count(self, room_id: str) -> int:
        """Every persisted artifact — tombstoned or not. Messages and
        attachments carry content; mentions/reactions/pins annotate it;
        read markers prove the history was seen. Block on doubt (R-1)."""
        row = self.fetch_one(
            f"""SELECT (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_messages
                    WHERE room_id = %s::uuid
                ) + (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_attachments
                    WHERE room_id = %s::uuid
                ) + (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_mentions mn
                    JOIN {_S}.tm_interaction_messages m ON m.id = mn.message_id
                    WHERE m.room_id = %s::uuid
                ) + (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_reactions rc
                    JOIN {_S}.tm_interaction_messages m ON m.id = rc.message_id
                    WHERE m.room_id = %s::uuid
                ) + (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_pins
                    WHERE room_id = %s::uuid
                ) + (
                    SELECT COUNT(*) FROM {_S}.tm_interaction_reads
                    WHERE room_id = %s::uuid
                ) AS total""",
            (room_id,) * 6,
        )
        return int((row or {}).get("total") or 0)

    def process_exists(self, processo_id: str) -> bool:
        row = self.fetch_one(
            f"""SELECT processo_id FROM {_S}.processos
                WHERE processo_id = %s::uuid AND deletado = FALSE""",
            (processo_id,),
        )
        return row is not None

    @staticmethod
    def _is_primary_conflict(exc: PluginsRepositoryError) -> bool:
        """Unique-violation backstop: the partial index on active primary
        links is the final arbiter under races."""
        cause = exc.__cause__
        return type(cause).__name__ == "UniqueViolation" or (
            "uq_tm_interaction_room_links_primary_active" in str(exc)
            or "uq_tm_interaction_rooms_processo_active" in str(exc)
        )

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
                WHERE base.deleted_at IS NULL
                ORDER BY COALESCE(base.last_message_at, base.updated_at) DESC, base.id DESC""",
            (viewer, viewer, viewer, viewer),
        )
        rooms = [_room(row) for row in rows]
        self._attach_graphs(rooms)
        if inbox_filter == "unread":
            return [room for room in rooms if room.unread_count > 0]
        if inbox_filter == "mentioned":
            return [room for room in rooms if room.mentioned]
        return rooms

    def _attach_graphs(self, rooms: list[InteractionRoom]) -> None:
        """Bulk-load active links + participants for a room list — no N+1."""
        if not rooms:
            return
        ids = [room.id for room in rooms]
        link_rows = self.fetch_all(
            f"""SELECT id, room_id, entity_type, entity_key, link_role,
                       created_by_user_id, created_at, deleted_at, deleted_cause
                FROM {_S}.tm_interaction_room_links
                WHERE room_id = ANY(%s::uuid[]) AND deleted_at IS NULL
                ORDER BY created_at ASC, id ASC""",
            (ids,),
        )
        participant_rows = self.fetch_all(
            f"""SELECT room_id, user_id, role, added_by_user_id,
                       created_at, removed_at
                FROM {_S}.tm_interaction_room_participants
                WHERE room_id = ANY(%s::uuid[]) AND removed_at IS NULL
                ORDER BY created_at ASC, user_id ASC""",
            (ids,),
        )
        links: dict[str, list[InteractionRoomLink]] = defaultdict(list)
        participants: dict[str, list[InteractionRoomParticipant]] = defaultdict(list)
        for row in link_rows:
            links[str(row["room_id"])].append(_link(row))
        for row in participant_rows:
            participants[str(row["room_id"])].append(_participant(row))
        for index, room in enumerate(rooms):
            rooms[index] = replace(
                room,
                links=tuple(links.get(room.id, ())),
                participants=tuple(participants.get(room.id, ())),
            )

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
        with self.db() as connection:
            # Room-row lock first: serializes against guarded link
            # removal — the write either lands before the recount or
            # waits for the commit (R-1 TOCTOU).
            self._lock_room(connection, room_id)
            if parent_id:
                row = self.execute_returning_one(
                    f"""INSERT INTO {_S}.tm_interaction_messages
                            (room_id, author_user_id, content, parent_id)
                        VALUES (%s::uuid, %s::uuid, %s, %s::uuid)
                        RETURNING {_MESSAGE_COLUMNS}""",
                    (room_id, author_user_id, content, parent_id),
                    auto_commit=False,
                )
            else:
                row = self.execute_returning_one(
                    f"""INSERT INTO {_S}.tm_interaction_messages
                            (room_id, author_user_id, content)
                        VALUES (%s::uuid, %s::uuid, %s)
                        RETURNING {_MESSAGE_COLUMNS}""",
                    (room_id, author_user_id, content),
                    auto_commit=False,
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
                    auto_commit=False,
                )
            self.execute_returning_one(
                f"UPDATE {_S}.tm_interaction_rooms SET updated_at = NOW() WHERE id = %s::uuid RETURNING id",
                (room_id,),
                auto_commit=False,
            )
            connection.commit()
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
        with self.db() as connection:
            room = connection.execute(
                f"SELECT room_id FROM {_S}.tm_interaction_messages WHERE id = %s::uuid",
                (message_id,),
            ).fetchone()
            if room is not None:
                self._lock_room(connection, str(dict(room)["room_id"]))
            removed = self.execute_returning_one(
                f"""DELETE FROM {_S}.tm_interaction_reactions
                    WHERE message_id = %s::uuid AND user_id = %s::uuid AND code = %s
                    RETURNING code""",
                (message_id, user_id, code),
                auto_commit=False,
            )
            if removed is None:
                self.execute_returning_one(
                    f"""INSERT INTO {_S}.tm_interaction_reactions (message_id, user_id, code)
                        VALUES (%s::uuid, %s::uuid, %s)
                        RETURNING code""",
                    (message_id, user_id, code),
                    auto_commit=False,
                )
            connection.commit()

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None:
        with self.db() as connection:
            self._lock_room(connection, room_id)
            self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_pins (room_id, message_id, pinned_by_user_id)
                    VALUES (%s::uuid, %s::uuid, %s::uuid)
                    ON CONFLICT (room_id, message_id) DO NOTHING
                    RETURNING id""",
                (room_id, message_id, user_id),
                auto_commit=False,
            )
            connection.commit()

    def unpin_message(self, *, room_id: str, message_id: str) -> None:
        with self.db() as connection:
            self._lock_room(connection, room_id)
            self.execute(
                f"""DELETE FROM {_S}.tm_interaction_pins
                    WHERE room_id = %s::uuid AND message_id = %s::uuid""",
                (room_id, message_id),
                auto_commit=False,
            )
            connection.commit()

    def mark_read(self, *, room_id: str, user_id: str) -> None:
        with self.db() as connection:
            self._lock_room(connection, room_id)
            self.execute_returning_one(
                f"""INSERT INTO {_S}.tm_interaction_reads (room_id, user_id, last_read_at)
                    VALUES (%s::uuid, %s::uuid, NOW())
                    ON CONFLICT (room_id, user_id) DO UPDATE SET last_read_at = NOW()
                    RETURNING room_id""",
                (room_id, user_id),
                auto_commit=False,
            )
            connection.commit()

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment:
        with self.db() as connection:
            self._lock_room(connection, attachment.room_id)
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
                auto_commit=False,
            )
            connection.commit()
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
        self.links: dict[str, InteractionRoomLink] = {}
        self.participants: dict[tuple[str, str], InteractionRoomParticipant] = {}
        self.messages: dict[str, InteractionMessage] = {}
        self.attachments: dict[str, InteractionAttachment] = {}
        self.pins: set[tuple[str, str]] = set()
        self.reads: dict[tuple[str, str], datetime] = {}
        self._locks: dict[str, threading.Lock] = {}

    def get_by_process(self, processo_id: str) -> InteractionRoom | None:
        room_id = self.by_process.get(processo_id)
        if room_id is None:
            return None
        room = self.rooms[room_id]
        if room.deleted_at is not None:
            return None
        return self._graph(room)

    def create_room_graph(
        self,
        *,
        title: str | None,
        access_scope: str,
        created_by_user_id: str,
        processo_id: str | None = None,
        links: tuple[tuple[str, str, str], ...] = (),
        owner_participant: bool = False,
        participant_ids: tuple[str, ...] = (),
    ) -> InteractionRoom | None:
        """Check-first then mutate — all-or-nothing like the SQL tx."""
        if processo_id is not None and processo_id not in self.processes:
            return None
        for entity_type, entity_key, link_role in links:
            if link_role == "primary" and self._active_primary_holder(
                entity_type, entity_key
            ) is not None:
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                )
        now = datetime.now(timezone.utc)
        room = InteractionRoom(
            id=str(uuid4()),
            processo_id=processo_id,
            processo_codigo="PROC" if processo_id else "",
            processo_nome="Processo" if processo_id else "",
            created_by_user_id=created_by_user_id,
            created_at=now,
            updated_at=now,
            access_scope=access_scope,
            title=title,
        )
        self.rooms[room.id] = room
        if processo_id:
            self.by_process[processo_id] = room.id
        for entity_type, entity_key, link_role in links:
            link = InteractionRoomLink(
                id=str(uuid4()),
                room_id=room.id,
                entity_type=entity_type,
                entity_key=entity_key,
                link_role=link_role,
                created_by_user_id=created_by_user_id,
                created_at=now,
            )
            self.links[link.id] = link
        member_ids = list(participant_ids)
        if owner_participant:
            member_ids.insert(0, created_by_user_id)
        for member_id in dict.fromkeys(member_ids):
            self.add_participant(
                room_id=room.id,
                user_id=member_id,
                role="owner" if member_id == created_by_user_id else "member",
                actor_user_id=created_by_user_id,
            )
        return self._graph(room)

    def get(self, room_id: str) -> InteractionRoom | None:
        room = self.rooms.get(room_id)
        if room is None or room.deleted_at is not None:
            return None
        return self._graph(room)

    def get_raw(self, room_id: str) -> InteractionRoom | None:
        room = self.rooms.get(room_id)
        if room is None:
            return None
        return self._graph(room, include_inactive_links=True, include_removed=True)

    def _graph(
        self,
        room: InteractionRoom,
        *,
        include_inactive_links: bool = False,
        include_removed: bool = False,
    ) -> InteractionRoom:
        links = tuple(
            link
            for link in self.links.values()
            if link.room_id == room.id
            and (include_inactive_links or link.deleted_at is None)
        )
        participants = tuple(
            item
            for item in self.participants.values()
            if item.room_id == room.id and (include_removed or item.removed_at is None)
        )
        return replace(room, links=links, participants=participants)

    def soft_delete(
        self, room_id: str, *, actor_user_id: str | None = None
    ) -> InteractionRoom | None:
        room = self.rooms.get(room_id)
        if room is None or room.deleted_at is not None:
            return None
        now = datetime.now(timezone.utc)
        deleted = replace(
            room,
            deleted_at=now,
            deleted_by_user_id=actor_user_id,
            updated_at=now,
        )
        self.rooms[room_id] = deleted
        for link_id, link in self.links.items():
            if link.room_id == room_id and link.deleted_at is None:
                self.links[link_id] = replace(
                    link, deleted_at=now, deleted_cause=LINK_DELETED_ROOM_DELETED
                )
        return self._graph(deleted, include_inactive_links=True)

    def restore_room(self, room_id: str) -> InteractionRoom | None:
        room = self.rooms.get(room_id)
        if room is None or room.deleted_at is None:
            return None
        now = datetime.now(timezone.utc)
        revivable = [
            link
            for link in self.links.values()
            if link.room_id == room_id
            and link.deleted_cause == LINK_DELETED_ROOM_DELETED
        ]
        for link in revivable:
            if link.link_role == "primary":
                holder = self._active_primary_holder(link.entity_type, link.entity_key)
                if holder is not None and holder != room_id:
                    raise PrimaryLinkConflict(
                        "O objeto já possui outra sala primária ativa."
                    )
        self.rooms[room_id] = replace(
            room, deleted_at=None, deleted_by_user_id=None, updated_at=now
        )
        for link in revivable:
            self.links[link.id] = replace(link, deleted_at=None, deleted_cause=None)
        return self._graph(self.rooms[room_id], include_inactive_links=True)

    # --- typed links --------------------------------------------------------

    def list_links(
        self, room_id: str, *, include_inactive: bool = False
    ) -> list[InteractionRoomLink]:
        return [
            link
            for link in self.links.values()
            if link.room_id == room_id
            and (include_inactive or link.deleted_at is None)
        ]

    def _active_primary_holder(self, entity_type: str, entity_key: str) -> str | None:
        for link in self.links.values():
            if (
                link.entity_type == entity_type
                and link.entity_key == entity_key
                and link.link_role == "primary"
                and link.deleted_at is None
            ):
                room = self.rooms.get(link.room_id)
                if room is not None and room.deleted_at is None:
                    return link.room_id
        return None

    def find_active_primary_room(
        self, entity_type: str, entity_key: str
    ) -> InteractionRoom | None:
        room_id = self._active_primary_holder(entity_type, entity_key)
        if room_id is None:
            return None
        return self._graph(self.rooms[room_id])

    def upsert_link(
        self,
        *,
        room_id: str,
        entity_type: str,
        entity_key: str,
        link_role: str,
        actor_user_id: str,
    ) -> InteractionRoomLink:
        if link_role == "primary":
            holder = self._active_primary_holder(entity_type, entity_key)
            if holder is not None and holder != room_id:
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                )
        existing = next(
            (
                link
                for link in self.links.values()
                if link.room_id == room_id
                and link.entity_type == entity_type
                and link.entity_key == entity_key
            ),
            None,
        )
        now = datetime.now(timezone.utc)
        if existing is not None:
            revived = replace(
                existing,
                link_role=link_role,
                deleted_at=None,
                deleted_cause=None,
            )
            self.links[existing.id] = revived
            return revived
        link = InteractionRoomLink(
            id=str(uuid4()),
            room_id=room_id,
            entity_type=entity_type,
            entity_key=entity_key,
            link_role=link_role,
            created_by_user_id=actor_user_id,
            created_at=now,
        )
        self.links[link.id] = link
        return link

    def tombstone_link(self, link_id: str, *, cause: str) -> InteractionRoomLink | None:
        link = self.links.get(link_id)
        if link is None or link.deleted_at is not None:
            return None
        tombstoned = replace(
            link, deleted_at=datetime.now(timezone.utc), deleted_cause=cause
        )
        self.links[link_id] = tombstoned
        return tombstoned

    def _room_lock(self, room_id: str) -> threading.Lock:
        """Per-room mutex — InMemory twin of ``SELECT ... FOR UPDATE`` so
        the same lock ordering is exercised by the double."""
        return self._locks.setdefault(room_id, threading.Lock())

    def tombstone_link_guarded(
        self, *, room_id: str, link_id: str, cause: str
    ) -> InteractionRoomLink | None:
        with self._room_lock(room_id):
            if self.protected_content_count(room_id) > 0:
                raise RoomAccessExpansionBlocked(
                    "A remoção ampliaria o acesso ao histórico protegido."
                )
            link = self.links.get(link_id)
            if (
                link is None
                or link.room_id != room_id
                or link.deleted_at is not None
            ):
                return None
            tombstoned = replace(
                link, deleted_at=datetime.now(timezone.utc), deleted_cause=cause
            )
            self.links[link_id] = tombstoned
            return tombstoned

    # --- participants -------------------------------------------------------

    def is_participant(self, room_id: str, user_id: str) -> bool:
        item = self.participants.get((room_id, user_id))
        return item is not None and item.removed_at is None

    def add_participant(
        self, *, room_id: str, user_id: str, role: str, actor_user_id: str
    ) -> InteractionRoomParticipant:
        key = (room_id, user_id)
        existing = self.participants.get(key)
        if existing is not None:
            revived = replace(existing, role=role, removed_at=None, added_by_user_id=actor_user_id)
            self.participants[key] = revived
            return revived
        item = InteractionRoomParticipant(
            room_id=room_id,
            user_id=user_id,
            role=role,
            added_by_user_id=actor_user_id,
            created_at=datetime.now(timezone.utc),
        )
        self.participants[key] = item
        return item

    def remove_participant(self, *, room_id: str, user_id: str) -> None:
        key = (room_id, user_id)
        item = self.participants.get(key)
        if item is not None and item.removed_at is None:
            self.participants[key] = replace(item, removed_at=datetime.now(timezone.utc))

    def list_participants(
        self, room_id: str, *, active_only: bool = True
    ) -> list[InteractionRoomParticipant]:
        return [
            item
            for (rid, _), item in self.participants.items()
            if rid == room_id and (not active_only or item.removed_at is None)
        ]

    # --- authorization support ----------------------------------------------

    def protected_content_count(self, room_id: str) -> int:
        """Parity with the SQL adapter: every persisted artifact, including
        tombstoned messages, attachments, embedded mentions/reactions,
        pins and read markers."""
        messages = [m for m in self.messages.values() if m.room_id == room_id]
        return (
            len(messages)
            + sum(len(m.mentions) + len(m.reactions) for m in messages)
            + sum(1 for item in self.attachments.values() if item.room_id == room_id)
            + sum(1 for rid, _mid in self.pins if rid == room_id)
            + sum(1 for rid, _uid in self.reads if rid == room_id)
        )

    def process_exists(self, processo_id: str) -> bool:
        return processo_id in self.processes

    def list_rooms(
        self,
        *,
        viewer_user_id: str | None = None,
        inbox_filter: str = "all",
    ) -> list[InteractionRoom]:
        rooms = sorted(
            (room for room in self.rooms.values() if room.deleted_at is None),
            key=lambda room: room.updated_at or datetime.min,
            reverse=True,
        )
        visible: list[InteractionRoom] = []
        for room in rooms:
            unread, mentioned = self._signals(room.id, viewer_user_id)
            shown = replace(
                self._graph(room), unread_count=unread, mentioned=mentioned
            )
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
        with self._room_lock(room_id):
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
        with self._room_lock(message.room_id):
            current = list(message.reactions)
            kept = [item for item in current if not (item.user_id == user_id and item.code == code)]
            if len(kept) == len(current):
                kept.append(InteractionReaction(user_id=user_id, code=code))
            self.messages[message_id] = replace(message, reactions=tuple(kept))

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None:
        del user_id
        with self._room_lock(room_id):
            self.pins.add((room_id, message_id))

    def unpin_message(self, *, room_id: str, message_id: str) -> None:
        with self._room_lock(room_id):
            self.pins.discard((room_id, message_id))

    def mark_read(self, *, room_id: str, user_id: str) -> None:
        with self._room_lock(room_id):
            self.reads[(room_id, user_id)] = datetime.now(timezone.utc)

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment:
        stored = replace(
            attachment,
            id=attachment.id or str(uuid4()),
            created_at=attachment.created_at or datetime.now(timezone.utc),
        )
        with self._room_lock(stored.room_id):
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
