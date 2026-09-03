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

    def latest_recorded_at(self, device_id: UUID) -> datetime | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT recorded_at
                    FROM production_pulse.readings
                    WHERE device_id = %s
                    ORDER BY recorded_at DESC, id DESC
                    LIMIT 1
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        value = row["recorded_at"]
        return value if isinstance(value, datetime) else None

    def list_for_device(
        self,
        device_id: UUID,
        *,
        page: int,
        page_size: int,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
        metric_key: str | None = None,
        sample_interval_ms: int | None = None,
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
        interval_ms = (
            int(sample_interval_ms)
            if sample_interval_ms is not None and int(sample_interval_ms) > 0
            else None
        )

        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM production_pulse.readings WHERE {where_sql}",
                    params,
                )
                total = int(cur.fetchone()["total"])
                if interval_ms is None:
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
                else:
                    # Uma leitura por bucket temporal — cobre o intervalo inteiro no gráfico.
                    cur.execute(
                        f"""
                        WITH filtered AS (
                            SELECT {_READING_COLUMNS},
                                   FLOOR(
                                       EXTRACT(EPOCH FROM recorded_at) * 1000 / %s
                                   )::bigint AS sample_bucket
                            FROM production_pulse.readings
                            WHERE {where_sql}
                        ),
                        ranked AS (
                            SELECT
                                id, device_id, metrics, delta_metrics, meta, source,
                                recorded_at, created_at,
                                ROW_NUMBER() OVER (
                                    PARTITION BY sample_bucket
                                    ORDER BY recorded_at DESC, id DESC
                                ) AS rn
                            FROM filtered
                        )
                        SELECT
                            id, device_id, metrics, delta_metrics, meta, source,
                            recorded_at, created_at
                        FROM ranked
                        WHERE rn = 1
                        ORDER BY recorded_at DESC, id DESC
                        LIMIT %s OFFSET %s
                        """,
                        [interval_ms, *params, page_size, offset],
                    )
                rows = list(cur.fetchall())
        return rows, total

    def delete_older_than(
        self,
        *,
        cutoff: datetime,
        batch_size: int = 5_000,
    ) -> int:
        """Remove raw readings older than cutoff (R49). Returns deleted row count."""
        limit = max(1, min(int(batch_size), 50_000))
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH doomed AS (
                        SELECT id
                        FROM production_pulse.readings
                        WHERE recorded_at < %s
                        ORDER BY recorded_at ASC, id ASC
                        LIMIT %s
                    )
                    DELETE FROM production_pulse.readings r
                    USING doomed
                    WHERE r.id = doomed.id
                    """,
                    (cutoff, limit),
                )
                deleted = cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else 0
            conn.commit()
        return int(deleted)

    def sum_delta_metric_for_devices(
        self,
        device_ids: list[UUID],
        *,
        metric_key: str,
        recorded_from: datetime,
        recorded_to: datetime,
    ) -> dict[UUID, int]:
        if not device_ids:
            return {}

        normalized_key = (metric_key or "").strip()
        if not normalized_key:
            return {}

        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT device_id,
                           COALESCE(SUM((delta_metrics->>%s)::bigint), 0) AS total
                    FROM production_pulse.readings
                    WHERE device_id = ANY(%s::uuid[])
                      AND recorded_at >= %s
                      AND recorded_at < %s
                      AND delta_metrics ? %s
                    GROUP BY device_id
                    """,
                    (
                        normalized_key,
                        device_ids,
                        recorded_from,
                        recorded_to,
                        normalized_key,
                    ),
                )
                rows = list(cur.fetchall())

        return {row["device_id"]: int(row["total"]) for row in rows}
