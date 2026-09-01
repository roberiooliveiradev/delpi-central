from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_READING_COLUMNS = """
    id, device_id, metrics, delta_metrics, meta, source, recorded_at, created_at
"""


class PostgresDeviceReadingRepository:
    def insert(
        self,
        device_id: UUID,
        *,
        metrics: dict[str, Any],
        delta_metrics: dict[str, Any],
        meta: dict[str, Any],
        source: str,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                if recorded_at is None:
                    cur.execute(
                        f"""
                        INSERT INTO production_pulse.readings (
                            device_id, metrics, delta_metrics, meta, source
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING {_READING_COLUMNS}
                        """,
                        (
                            device_id,
                            Json(metrics),
                            Json(delta_metrics),
                            Json(meta),
                            source,
                        ),
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT INTO production_pulse.readings (
                            device_id, metrics, delta_metrics, meta, source, recorded_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING {_READING_COLUMNS}
                        """,
                        (
                            device_id,
                            Json(metrics),
                            Json(delta_metrics),
                            Json(meta),
                            source,
                            recorded_at,
                        ),
                    )
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def count_for_device(self, device_id: UUID) -> int:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS total FROM production_pulse.readings WHERE device_id = %s",
                    (device_id,),
                )
                return int(cur.fetchone()["total"])

    def list_for_device(
        self,
        device_id: UUID,
        *,
        page: int,
        page_size: int,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
        metric_key: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["device_id = %s"]
        params: list[Any] = [device_id]

        if recorded_from is not None:
            clauses.append("recorded_at >= %s")
            params.append(recorded_from)
        if recorded_to is not None:
            clauses.append("recorded_at <= %s")
            params.append(recorded_to)
        if metric_key:
            clauses.append("metrics ? %s")
            params.append(metric_key.strip())

        where_sql = " AND ".join(clauses)
        offset = (page - 1) * page_size

        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM production_pulse.readings WHERE {where_sql}",
                    params,
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"""
                    SELECT {_READING_COLUMNS}
                    FROM production_pulse.readings
                    WHERE {where_sql}
                    ORDER BY recorded_at DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, page_size, offset],
                )
                rows = list(cur.fetchall())
        return rows, total
