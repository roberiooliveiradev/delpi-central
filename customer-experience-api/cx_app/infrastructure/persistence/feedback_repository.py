from __future__ import annotations

from typing import Any

from cx_app.infrastructure.persistence.plugins_postgres_connection import (
    CX_SCHEMA_NAME,
    get_connection,
)

_TABLE = f'"{CX_SCHEMA_NAME}".feedback'

_COLUMNS = "id, participant_id, rating, liked_most, suggestions, created_at"


class FeedbackRepository:
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_TABLE}
                        (participant_id, rating, liked_most, suggestions)
                    VALUES
                        (%(participant_id)s, %(rating)s, %(liked_most)s, %(suggestions)s)
                    RETURNING {_COLUMNS}
                    """,
                    data,
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else {}

    def get_by_participant_id(self, participant_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNS} FROM {_TABLE} WHERE participant_id = %s",
                    (participant_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def exists_for_participant(self, participant_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT 1 FROM {_TABLE} WHERE participant_id = %s LIMIT 1",
                    (participant_id,),
                )
                return cur.fetchone() is not None
