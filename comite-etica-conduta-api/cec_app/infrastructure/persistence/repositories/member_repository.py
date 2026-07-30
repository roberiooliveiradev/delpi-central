from __future__ import annotations

from typing import Any

from cec_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    _uuid,
    get_connection,
)

LEADERSHIP_ROLES = frozenset({"president", "secretary"})
MEMBER_ROLES = frozenset({"president", "secretary", "member", "guest"})


class MemberRepository:
    def list_members(
        self,
        *,
        active_on: str | None = None,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        clauses = ["deleted_at IS NULL"]
        params: list[Any] = []
        if active_on:
            clauses.append("is_active = TRUE")
            clauses.append("mandate_start <= %s")
            clauses.append("(mandate_end IS NULL OR mandate_end >= %s)")
            params.extend([active_on, active_on])
        elif not include_inactive:
            clauses.append("is_active = TRUE")
        where = " AND ".join(clauses)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT *
                    FROM comite_etica.members
                    WHERE {where}
                    ORDER BY
                      CASE role
                        WHEN 'president' THEN 1
                        WHEN 'secretary' THEN 2
                        WHEN 'member' THEN 3
                        ELSE 4
                      END,
                      sort_order ASC,
                      display_name ASC,
                      mandate_start DESC
                    """,
                    params,
                )
                return cur.fetchall()

    def get_member(self, member_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM comite_etica.members
                    WHERE id = %s AND deleted_at IS NULL
                    """,
                    (_uuid(member_id),),
                )
                return cur.fetchone()

    def find_active_by_user(
        self, *, user_id: str, exclude_id: str | None = None
    ) -> dict[str, Any] | None:
        clauses = ["deleted_at IS NULL", "is_active = TRUE", "user_id = %s"]
        params: list[Any] = [_uuid(user_id)]
        if exclude_id:
            clauses.append("id <> %s")
            params.append(_uuid(exclude_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT * FROM comite_etica.members WHERE {' AND '.join(clauses)} LIMIT 1",
                    params,
                )
                return cur.fetchone()

    def find_active_leadership(
        self, *, role: str, exclude_id: str | None = None
    ) -> dict[str, Any] | None:
        if role not in LEADERSHIP_ROLES:
            return None
        clauses = ["deleted_at IS NULL", "is_active = TRUE", "role = %s"]
        params: list[Any] = [role]
        if exclude_id:
            clauses.append("id <> %s")
            params.append(_uuid(exclude_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT * FROM comite_etica.members WHERE {' AND '.join(clauses)} LIMIT 1",
                    params,
                )
                return cur.fetchone()

    def create_member(
        self,
        *,
        user_id: str,
        display_name: str,
        role: str,
        mandate_start: str,
        mandate_end: str | None,
        sort_order: int,
        actor_user_id: str,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO comite_etica.members (
                        user_id, display_name, role, mandate_start, mandate_end,
                        is_active, sort_order, created_by_user_id, updated_by_user_id
                    ) VALUES (%s,%s,%s,%s,%s,TRUE,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        _uuid(user_id),
                        display_name,
                        role,
                        mandate_start,
                        mandate_end,
                        sort_order,
                        _uuid(actor_user_id),
                        _uuid(actor_user_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return row

    def update_member(
        self,
        *,
        member_id: str,
        fields: dict[str, Any],
        actor_user_id: str,
    ) -> dict[str, Any]:
        allowed = {
            "display_name",
            "role",
            "mandate_start",
            "mandate_end",
            "is_active",
            "sort_order",
        }
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        if not sets:
            member = self.get_member(member_id)
            if not member:
                raise LookupError("Membro não encontrado.")
            return member
        sets.append("updated_by_user_id = %s")
        params.append(_uuid(actor_user_id))
        sets.append("updated_at = NOW()")
        params.append(_uuid(member_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE comite_etica.members
                    SET {', '.join(sets)}
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    params,
                )
                row = cur.fetchone()
                if not row:
                    raise LookupError("Membro não encontrado.")
            conn.commit()
            return row

    def soft_delete(self, *, member_id: str, actor_user_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE comite_etica.members
                    SET deleted_at = NOW(),
                        is_active = FALSE,
                        updated_by_user_id = %s,
                        updated_at = NOW()
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    (_uuid(actor_user_id), _uuid(member_id)),
                )
                row = cur.fetchone()
                if not row:
                    raise LookupError("Membro não encontrado.")
            conn.commit()
            return row
