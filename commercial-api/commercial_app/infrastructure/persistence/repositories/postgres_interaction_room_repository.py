from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.interaction_room import (
    InteractionRoom,
    InteractionRoomMember,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_ROOM_COLUMNS = """
    id, kind, entity_type, entity_key, group_id, title,
    created_by_user_id, created_at, updated_at, deleted_at
"""

_MEMBER_COLUMNS = """
    id, room_id, user_id, role, last_read_at, muted, created_at
"""


def _row_room(row: dict[str, Any] | None) -> InteractionRoom | None:
    if not row:
        return None
    return InteractionRoom(
        id=row["id"],
        kind=row["kind"],
        entity_type=row.get("entity_type"),
        entity_key=row.get("entity_key"),
        group_id=row.get("group_id"),
        title=row["title"],
        created_by_user_id=row["created_by_user_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row.get("deleted_at"),
    )


def _row_member(row: dict[str, Any] | None) -> InteractionRoomMember | None:
    if not row:
        return None
    return InteractionRoomMember(
        id=row["id"],
        room_id=row["room_id"],
        user_id=row["user_id"],
        role=row["role"],
        last_read_at=row.get("last_read_at"),
        muted=bool(row.get("muted")),
        created_at=row["created_at"],
    )


class PostgresInteractionRoomRepository(
    PluginBaseRepository,
    InteractionRoomRepositoryPort,
):
    def get_by_id(self, room_id: UUID) -> InteractionRoom | None:
        row = self.fetch_one(
            f"""
            SELECT {_ROOM_COLUMNS}
              FROM commercial.interaction_rooms
             WHERE id = %s
               AND deleted_at IS NULL
            """,
            (str(room_id),),
        )
        return _row_room(row)

    def find_entity_room(
        self,
        *,
        entity_type: str,
        entity_key: str,
    ) -> InteractionRoom | None:
        row = self.fetch_one(
            f"""
            SELECT {_ROOM_COLUMNS}
              FROM commercial.interaction_rooms
             WHERE kind = 'entity'
               AND entity_type = %s
               AND entity_key = %s
               AND deleted_at IS NULL
            """,
            (entity_type.strip(), entity_key.strip()),
        )
        return _row_room(row)

    def find_wall_room(self, *, group_id: UUID | None = None) -> InteractionRoom | None:
        if group_id is None:
            row = self.fetch_one(
                f"""
                SELECT {_ROOM_COLUMNS}
                  FROM commercial.interaction_rooms
                 WHERE kind = 'wall'
                   AND group_id IS NULL
                   AND deleted_at IS NULL
                """,
            )
            return _row_room(row)
        row = self.fetch_one(
            f"""
            SELECT {_ROOM_COLUMNS}
              FROM commercial.interaction_rooms
             WHERE kind = 'wall'
               AND group_id = %s
               AND deleted_at IS NULL
            """,
            (str(group_id),),
        )
        return _row_room(row)

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
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.interaction_rooms (
                kind, entity_type, entity_key, group_id, title, created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING {_ROOM_COLUMNS}
            """,
            (
                kind.strip(),
                (entity_type or "").strip() or None,
                (entity_key or "").strip() or None,
                str(group_id) if group_id else None,
                title.strip(),
                created_by_user_id.strip(),
            ),
        )
        room = _row_room(row)
        if room is None:
            raise RuntimeError("Falha ao criar sala de interação.")
        return room

    def touch_updated_at(self, room_id: UUID) -> InteractionRoom | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.interaction_rooms
               SET updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
         RETURNING {_ROOM_COLUMNS}
            """,
            (str(room_id),),
        )
        return _row_room(row)

    def list_for_user(
        self,
        *,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InteractionRoom]:
        rows = self.fetch_all(
            f"""
            SELECT r.id, r.kind, r.entity_type, r.entity_key, r.group_id, r.title,
                   r.created_by_user_id, r.created_at, r.updated_at, r.deleted_at
              FROM commercial.interaction_rooms r
              INNER JOIN commercial.interaction_room_members m
                      ON m.room_id = r.id
             WHERE m.user_id = %s
               AND r.deleted_at IS NULL
             ORDER BY r.updated_at DESC
             LIMIT %s OFFSET %s
            """,
            (
                user_id.strip(),
                max(1, min(int(limit), 200)),
                max(0, int(offset)),
            ),
        )
        return [room for row in rows if (room := _row_room(row)) is not None]

    def list_members(self, room_id: UUID) -> Sequence[InteractionRoomMember]:
        rows = self.fetch_all(
            f"""
            SELECT {_MEMBER_COLUMNS}
              FROM commercial.interaction_room_members
             WHERE room_id = %s
             ORDER BY created_at ASC
            """,
            (str(room_id),),
        )
        return [member for row in rows if (member := _row_member(row)) is not None]

    def get_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
    ) -> InteractionRoomMember | None:
        row = self.fetch_one(
            f"""
            SELECT {_MEMBER_COLUMNS}
              FROM commercial.interaction_room_members
             WHERE room_id = %s
               AND user_id = %s
            """,
            (str(room_id), user_id.strip()),
        )
        return _row_member(row)

    def add_member(
        self,
        *,
        room_id: UUID,
        user_id: str,
        role: str = "member",
    ) -> InteractionRoomMember:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.interaction_room_members (room_id, user_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (room_id, user_id) DO UPDATE
               SET role = EXCLUDED.role
         RETURNING {_MEMBER_COLUMNS}
            """,
            (str(room_id), user_id.strip(), (role or "member").strip() or "member"),
        )
        member = _row_member(row)
        if member is None:
            raise RuntimeError("Falha ao adicionar membro da sala.")
        return member

    def remove_member(self, *, room_id: UUID, user_id: str) -> bool:
        row = self.execute_returning_one(
            """
            DELETE FROM commercial.interaction_room_members
             WHERE room_id = %s
               AND user_id = %s
         RETURNING id
            """,
            (str(room_id), user_id.strip()),
        )
        return row is not None

    def mark_read(
        self,
        *,
        room_id: UUID,
        user_id: str,
        read_at: datetime | None = None,
    ) -> InteractionRoomMember | None:
        if read_at is None:
            row = self.execute_returning_one(
                f"""
                UPDATE commercial.interaction_room_members
                   SET last_read_at = NOW()
                 WHERE room_id = %s
                   AND user_id = %s
             RETURNING {_MEMBER_COLUMNS}
                """,
                (str(room_id), user_id.strip()),
            )
        else:
            row = self.execute_returning_one(
                f"""
                UPDATE commercial.interaction_room_members
                   SET last_read_at = %s
                 WHERE room_id = %s
                   AND user_id = %s
             RETURNING {_MEMBER_COLUMNS}
                """,
                (read_at, str(room_id), user_id.strip()),
            )
        return _row_member(row)
