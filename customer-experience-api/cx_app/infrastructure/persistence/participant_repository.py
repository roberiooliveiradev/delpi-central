from __future__ import annotations

from datetime import date
from typing import Any

from cx_app.infrastructure.persistence.plugins_postgres_connection import (
    CX_SCHEMA_NAME,
    get_connection,
)

_TABLE = f'"{CX_SCHEMA_NAME}".participants'

_COLUMNS = (
    "id, public_token, full_name, company_name, visit_date, participant_info, "
    "photo_filename, photo_mime, qr_filename, feedback_qr_filename, thank_you_message, "
    "view_count, is_active, created_by, created_by_name, created_at, updated_at"
)


class ParticipantRepository:
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_TABLE}
                        (public_token, full_name, company_name, visit_date,
                         participant_info, photo_filename, photo_mime, qr_filename,
                         feedback_qr_filename, thank_you_message, created_by, created_by_name)
                    VALUES
                        (%(public_token)s, %(full_name)s, %(company_name)s, %(visit_date)s,
                         %(participant_info)s, %(photo_filename)s, %(photo_mime)s, %(qr_filename)s,
                         %(feedback_qr_filename)s, %(thank_you_message)s, %(created_by)s, %(created_by_name)s)
                    RETURNING {_COLUMNS}
                    """,
                    data,
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else {}

    def get_by_id(self, participant_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNS} FROM {_TABLE} WHERE id = %s",
                    (participant_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNS} FROM {_TABLE} WHERE public_token = %s",
                    (token,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def list(
        self,
        *,
        limit: int,
        offset: int,
        company: str | None = None,
        visit_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if company:
            clauses.append("company_name ILIKE %(company)s")
            params["company"] = f"%{company}%"
        if visit_date:
            clauses.append("visit_date = %(visit_date)s")
            params["visit_date"] = visit_date

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) AS total FROM {_TABLE} {where}", params)
                total = int(cur.fetchone()["total"])

                cur.execute(
                    f"""
                    SELECT {_COLUMNS} FROM {_TABLE} {where}
                    ORDER BY created_at DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    {**params, "limit": limit, "offset": offset},
                )
                rows = [dict(row) for row in cur.fetchall()]
        return rows, total

    def update(self, participant_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        if not fields:
            return self.get_by_id(participant_id)

        set_parts = [f"{key} = %({key})s" for key in fields]
        set_parts.append("updated_at = NOW()")
        params = {**fields, "id": participant_id}

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_TABLE}
                    SET {', '.join(set_parts)}
                    WHERE id = %(id)s
                    RETURNING {_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def set_active(self, participant_id: str, is_active: bool) -> dict[str, Any] | None:
        return self.update(participant_id, {"is_active": is_active})

    def increment_view_count(self, token: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {_TABLE} SET view_count = view_count + 1 WHERE public_token = %s",
                    (token,),
                )
            conn.commit()
