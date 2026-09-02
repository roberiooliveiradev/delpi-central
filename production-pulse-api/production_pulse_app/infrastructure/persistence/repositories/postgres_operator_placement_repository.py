from __future__ import annotations

from typing import Any

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_DEVICE_BINDING_COLUMNS = """
    d.id,
    d.branch,
    d.name,
    d.ip_address,
    d.driver_key,
    d.role_key,
    d.enabled,
    d.poll_interval_ms,
    d.last_seen_at,
    d.last_poll_attempt_at,
    d.last_metrics,
    d.last_error,
    b.anchor_type,
    b.placement_label,
    b.placement_key
"""


class PostgresOperatorPlacementRepository:
    def list_bound_devices(
        self,
        *,
        branch: str,
        anchor_type: str | None = None,
        search: str | None = None,
        placement_key: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = [
            "d.enabled = TRUE",
            "d.branch = %s",
            "b.effective_to IS NULL",
        ]
        params: list[Any] = [branch]
        if anchor_type:
            clauses.append("b.anchor_type = %s")
            params.append(anchor_type)
        if placement_key:
            clauses.append("b.placement_key = %s")
            params.append(placement_key)
        if search:
            pattern = f"%{search.strip()}%"
            clauses.append("(b.placement_label ILIKE %s OR d.name ILIKE %s)")
            params.extend([pattern, pattern])
        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT {_DEVICE_BINDING_COLUMNS}
            FROM production_pulse.devices d
            INNER JOIN production_pulse.device_bindings b ON b.device_id = d.id
            WHERE {where_sql}
            ORDER BY b.placement_label, d.name
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
