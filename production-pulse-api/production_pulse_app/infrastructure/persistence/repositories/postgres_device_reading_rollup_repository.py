from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_ROLLUP_COLUMNS = """
    id, device_id, bucket_start, resolution, metrics, delta_metrics, samples,
    created_at, updated_at
"""


def truncate_bucket_start(recorded_at: datetime, resolution: str) -> datetime:
    value = recorded_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    if resolution == "day":
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    return value.replace(minute=0, second=0, microsecond=0)


class PostgresDeviceReadingRollupRepository:
    def get_bucket(
        self,
        device_id: UUID,
        *,
        resolution: str,
        bucket_start: datetime,
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ROLLUP_COLUMNS}
                    FROM production_pulse.readings_rollups
                    WHERE device_id = %s
                      AND resolution = %s
                      AND bucket_start = %s
                    """,
                    (device_id, resolution, bucket_start),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def upsert_bucket(
        self,
        device_id: UUID,
        *,
        resolution: str,
        bucket_start: datetime,
        metrics: dict[str, Any],
        delta_metrics: dict[str, Any],
        samples: int,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.readings_rollups (
                        device_id, bucket_start, resolution, metrics, delta_metrics, samples
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_id, resolution, bucket_start)
                    DO UPDATE SET
                        metrics = EXCLUDED.metrics,
                        delta_metrics = EXCLUDED.delta_metrics,
                        samples = EXCLUDED.samples,
                        updated_at = NOW()
                    RETURNING {_ROLLUP_COLUMNS}
                    """,
                    (
                        device_id,
                        bucket_start,
                        resolution,
                        Json(metrics),
                        Json(delta_metrics),
                        max(0, int(samples)),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def list_for_device(
        self,
        device_id: UUID,
        *,
        resolution: str,
        page: int,
        page_size: int,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["device_id = %s", "resolution = %s"]
        params: list[Any] = [device_id, resolution]
        if recorded_from is not None:
            clauses.append("bucket_start >= %s")
            params.append(recorded_from)
        if recorded_to is not None:
            clauses.append("bucket_start <= %s")
            params.append(recorded_to)
        where_sql = " AND ".join(clauses)
        offset = (page - 1) * page_size

        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM production_pulse.readings_rollups WHERE {where_sql}",
                    params,
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"""
                    SELECT {_ROLLUP_COLUMNS}
                    FROM production_pulse.readings_rollups
                    WHERE {where_sql}
                    ORDER BY bucket_start DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, page_size, offset],
                )
                rows = list(cur.fetchall())
        return [dict(row) for row in rows], total
