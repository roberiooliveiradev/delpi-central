from __future__ import annotations

from typing import Any, Sequence

from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)
from commercial_app.domain.ports.commercial_group_repository_port import (
    CommercialGroupRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_GROUP_COLUMNS = "id, kind, name, active, sort_order, created_at, updated_at"
_MEMBER_COLUMNS = "user_id"


class PostgresCommercialGroupRepository(PluginBaseRepository, CommercialGroupRepositoryPort):
    """Operational groups ↔ members (M:N) in schema commercial."""

    def get_by_id(self, group_id: str) -> CommercialGroup | None:
        row = self.fetch_one(
            f"SELECT {_GROUP_COLUMNS} FROM commercial.commercial_groups WHERE id = %s",
            (group_id,),
        )
        return self._hydrate(row)

    def get_by_kind(self, kind: str) -> CommercialGroup | None:
        row = self.fetch_one(
            f"""
            SELECT {_GROUP_COLUMNS}
              FROM commercial.commercial_groups
             WHERE kind = %s
            """,
            (str(kind).strip(),),
        )
        return self._hydrate(row)

    def list_groups(self, *, active_only: bool = False) -> list[CommercialGroup]:
        if active_only:
            rows = self.fetch_all(
                f"""
                SELECT {_GROUP_COLUMNS}
                  FROM commercial.commercial_groups
                 WHERE active = TRUE
                 ORDER BY sort_order ASC, name ASC
                """
            )
        else:
            rows = self.fetch_all(
                f"""
                SELECT {_GROUP_COLUMNS}
                  FROM commercial.commercial_groups
                 ORDER BY active DESC, sort_order ASC, name ASC
                """
            )
        return [group for row in rows if (group := self._hydrate(row)) is not None]

    def create_group(
        self,
        *,
        kind: str,
        name: str,
        sort_order: int = 0,
        active: bool = True,
    ) -> CommercialGroup:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.commercial_groups (kind, name, sort_order, active)
            VALUES (%s, %s, %s, %s)
            RETURNING {_GROUP_COLUMNS}
            """,
            (str(kind).strip(), str(name).strip(), int(sort_order), bool(active)),
        )
        group = self._hydrate(row)
        if group is None:
            raise RuntimeError("Falha ao criar grupo operacional.")
        return group

    def rename_group(self, group_id: str, *, name: str) -> CommercialGroup | None:
        gid = str(group_id).strip()
        new_name = str(name).strip()
        if not gid or not new_name:
            return None
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.commercial_groups
               SET name = %s,
                   updated_at = NOW()
             WHERE id = %s
         RETURNING {_GROUP_COLUMNS}
            """,
            (new_name, gid),
        )
        return self._hydrate(row)

    def delete_group(self, group_id: str) -> bool:
        gid = str(group_id).strip()
        if not gid:
            return False
        if self.fetch_one(
            "SELECT id FROM commercial.commercial_groups WHERE id = %s",
            (gid,),
        ) is None:
            return False
        self.execute(
            "DELETE FROM commercial.commercial_groups WHERE id = %s",
            (gid,),
        )
        return True

    def replace_members(
        self,
        *,
        group_id: str,
        members: Sequence[CommercialGroupMember],
    ) -> CommercialGroup | None:
        if self.fetch_one(
            "SELECT id FROM commercial.commercial_groups WHERE id = %s",
            (group_id,),
        ) is None:
            return None
        seen: set[str] = set()
        unique_ids: list[str] = []
        for member in members:
            uid = str(member.user_id).strip()
            if not uid or uid in seen:
                continue
            seen.add(uid)
            unique_ids.append(uid)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM commercial.commercial_group_members
                     WHERE group_id = %s
                    """,
                    (group_id,),
                )
                for uid in unique_ids:
                    cursor.execute(
                        """
                        INSERT INTO commercial.commercial_group_members (
                            group_id, user_id
                        ) VALUES (%s, %s)
                        ON CONFLICT (group_id, user_id) DO NOTHING
                        """,
                        (group_id, uid),
                    )
                cursor.execute(
                    """
                    UPDATE commercial.commercial_groups
                       SET updated_at = NOW()
                     WHERE id = %s
                    """,
                    (group_id,),
                )
            self.commit()
        except Exception:
            self.rollback()
            raise
        return self.get_by_id(group_id)

    def add_member(
        self,
        *,
        group_id: str,
        user_id: str,
    ) -> CommercialGroup | None:
        if self.fetch_one(
            "SELECT id FROM commercial.commercial_groups WHERE id = %s",
            (group_id,),
        ) is None:
            return None
        uid = str(user_id).strip()
        if not uid:
            return self.get_by_id(group_id)
        self.execute(
            """
            INSERT INTO commercial.commercial_group_members (group_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (group_id, user_id) DO NOTHING
            """,
            (group_id, uid),
        )
        self.execute(
            """
            UPDATE commercial.commercial_groups
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (group_id,),
        )
        return self.get_by_id(group_id)

    def remove_member(
        self,
        *,
        group_id: str,
        user_id: str,
    ) -> CommercialGroup | None:
        if self.fetch_one(
            "SELECT id FROM commercial.commercial_groups WHERE id = %s",
            (group_id,),
        ) is None:
            return None
        self.execute(
            """
            DELETE FROM commercial.commercial_group_members
             WHERE group_id = %s
               AND user_id = %s
            """,
            (group_id, str(user_id).strip()),
        )
        self.execute(
            """
            UPDATE commercial.commercial_groups
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (group_id,),
        )
        return self.get_by_id(group_id)

    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT user_id
              FROM commercial.commercial_group_members
             WHERE group_id = %s
             ORDER BY user_id ASC
            """,
            (group_id,),
        )
        return [str(row["user_id"]) for row in rows if row.get("user_id")]

    def list_groups_by_user_id(self, user_id: str) -> list[CommercialGroup]:
        rows = self.fetch_all(
            f"""
            SELECT g.id, g.kind, g.name, g.active, g.sort_order, g.created_at, g.updated_at
              FROM commercial.commercial_groups g
              INNER JOIN commercial.commercial_group_members m
                ON m.group_id = g.id
             WHERE m.user_id = %s
             ORDER BY g.sort_order ASC, g.name ASC
            """,
            (str(user_id).strip(),),
        )
        return [
            self._hydrate(row, include_members=False)
            for row in rows
            if row is not None
        ]

    def list_memberships_by_user_ids(
        self,
        user_ids: Sequence[str],
    ) -> list[tuple[str, CommercialGroup]]:
        normalized = [str(uid).strip() for uid in user_ids if str(uid).strip()]
        if not normalized:
            return []
        # Deduplicate while preserving order for stable roster joins.
        seen: set[str] = set()
        unique: list[str] = []
        for uid in normalized:
            if uid in seen:
                continue
            seen.add(uid)
            unique.append(uid)
        rows = self.fetch_all(
            f"""
            SELECT m.user_id AS member_user_id,
                   g.id, g.kind, g.name, g.active, g.sort_order,
                   g.created_at, g.updated_at
              FROM commercial.commercial_group_members m
              INNER JOIN commercial.commercial_groups g
                ON g.id = m.group_id
             WHERE m.user_id = ANY(%s)
             ORDER BY m.user_id ASC, g.sort_order ASC, g.name ASC
            """,
            (unique,),
        )
        result: list[tuple[str, CommercialGroup]] = []
        for row in rows:
            user_id = str(row.get("member_user_id") or "").strip()
            group = self._hydrate(row, include_members=False)
            if user_id and group is not None:
                result.append((user_id, group))
        return result

    def _list_members(self, group_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT {_MEMBER_COLUMNS}
              FROM commercial.commercial_group_members
             WHERE group_id = %s
             ORDER BY user_id ASC
            """,
            (group_id,),
        )

    def _hydrate(
        self,
        row: dict[str, Any] | None,
        *,
        include_members: bool = True,
    ) -> CommercialGroup | None:
        if not row:
            return None
        group_id = str(row["id"])
        members: tuple[CommercialGroupMember, ...] = ()
        if include_members:
            members = tuple(
                CommercialGroupMember(user_id=str(item["user_id"]))
                for item in self._list_members(group_id)
                if item.get("user_id")
            )
        return CommercialGroup(
            id=group_id,
            kind=str(row["kind"]),
            name=str(row["name"]),
            active=bool(row.get("active", True)),
            sort_order=int(row.get("sort_order") or 0),
            members=members,
        )
