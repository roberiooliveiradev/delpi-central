from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_COMMAND_COLUMNS = """
    id, device_id, command_key, issued_by, success, error_message,
    request_payload, response_payload, created_at
"""


class PostgresDeviceCommandRepository:
    def insert(
        self,
        device_id: UUID,
        *,
        command_key: str,
        issued_by: str,
        success: bool,
        error_message: str | None = None,
        request_payload: dict[str, Any] | None = None,
        response_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.device_commands (
                        device_id, command_key, issued_by, success, error_message,
                        request_payload, response_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING {_COMMAND_COLUMNS}
                    """,
                    (
                        device_id,
                        command_key,
                        issued_by,
                        success,
                        error_message,
                        Json(request_payload or {}),
                        Json(response_payload or {}),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def list_for_device(
        self,
        device_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (page - 1) * page_size
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM production_pulse.device_commands
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"""
                    SELECT {_COMMAND_COLUMNS}
                    FROM production_pulse.device_commands
                    WHERE device_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (device_id, page_size, offset),
                )
                rows = list(cur.fetchall())
        return rows, total
