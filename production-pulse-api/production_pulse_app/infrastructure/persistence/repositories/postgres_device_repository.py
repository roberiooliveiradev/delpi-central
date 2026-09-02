from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg.errors
from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class DeviceConflictError(Exception):
    pass


class DeviceNotFoundError(Exception):
    pass


_DEVICE_COLUMNS = """
    id, branch, name, ip_address, controller_code, driver_key, role_key, enabled,
    poll_interval_ms, last_seen_at, last_poll_attempt_at, next_poll_at,
    last_metrics, last_error, created_at, updated_at, created_by, updated_by
"""


class PostgresDeviceRepository:
    def list_devices(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        role_key: str | None = None,
        enabled: bool | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []
        if branch:
            clauses.append("branch = %s")
            params.append(branch)
        elif branches:
            clauses.append("branch = ANY(%s)")
            params.append(branches)
        if role_key:
            clauses.append("role_key = %s")
            params.append(role_key)
        if enabled is not None:
            clauses.append("enabled = %s")
            params.append(enabled)
        if search:
            clauses.append(
                "(name ILIKE %s OR host(ip_address)::text ILIKE %s OR COALESCE(controller_code, '') ILIKE %s)"
            )
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])
        where_sql = " AND ".join(clauses)
        query = f"""
            SELECT {_DEVICE_COLUMNS}
            FROM production_pulse.devices
            WHERE {where_sql}
            ORDER BY branch, name
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return list(cur.fetchall())

    def get_by_id(self, device_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DEVICE_COLUMNS}
                    FROM production_pulse.devices
                    WHERE id = %s
                    """,
                    (device_id,),
                )
                return cur.fetchone()

    def create(
        self,
        *,
        branch: str,
        name: str,
        ip_address: str,
        driver_key: str,
        role_key: str,
        enabled: bool,
        poll_interval_ms: int,
        controller_code: str | None = None,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO production_pulse.devices (
                            branch, name, ip_address, controller_code, driver_key, role_key,
                            enabled, poll_interval_ms, created_by, updated_by
                        )
                        VALUES (%s, %s, %s::inet, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING {_DEVICE_COLUMNS}
                        """,
                        (
                            branch,
                            name,
                            ip_address,
                            controller_code,
                            driver_key,
                            role_key,
                            enabled,
                            poll_interval_ms,
                            actor_sub,
                            actor_sub,
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
                return dict(row)
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise DeviceConflictError(
                    "Já existe dispositivo com este IP ou código de controlador nesta filial."
                ) from exc

    def replace(
        self,
        device_id: UUID,
        *,
        branch: str,
        name: str,
        ip_address: str,
        driver_key: str,
        role_key: str,
        enabled: bool,
        poll_interval_ms: int,
        controller_code: str | None = None,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE production_pulse.devices
                        SET branch = %s,
                            name = %s,
                            ip_address = %s::inet,
                            controller_code = %s,
                            driver_key = %s,
                            role_key = %s,
                            enabled = %s,
                            poll_interval_ms = %s,
                            updated_by = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING {_DEVICE_COLUMNS}
                        """,
                        (
                            branch,
                            name,
                            ip_address,
                            controller_code,
                            driver_key,
                            role_key,
                            enabled,
                            poll_interval_ms,
                            actor_sub,
                            device_id,
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise DeviceConflictError(
                    "Já existe dispositivo com este IP ou código de controlador nesta filial."
                ) from exc
            if row is None:
                raise DeviceNotFoundError(str(device_id))
            return dict(row)

    def patch(
        self,
        device_id: UUID,
        *,
        updates: dict[str, Any],
        actor_sub: str | None,
    ) -> dict[str, Any]:
        if not updates:
            row = self.get_by_id(device_id)
            if row is None:
                raise DeviceNotFoundError(str(device_id))
            return dict(row)

        column_map = {
            "branch": "branch",
            "name": "name",
            "ip_address": "ip_address",
            "controller_code": "controller_code",
            "driver_key": "driver_key",
            "role_key": "role_key",
            "enabled": "enabled",
            "poll_interval_ms": "poll_interval_ms",
        }
        set_parts: list[str] = []
        params: list[Any] = []
        for key, column in column_map.items():
            if key not in updates:
                continue
            if column == "ip_address":
                set_parts.append(f"{column} = %s::inet")
            else:
                set_parts.append(f"{column} = %s")
            params.append(updates[key])
        set_parts.append("updated_by = %s")
        params.append(actor_sub)
        set_parts.append("updated_at = NOW()")
        params.append(device_id)

        with plugins_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE production_pulse.devices
                        SET {", ".join(set_parts)}
                        WHERE id = %s
                        RETURNING {_DEVICE_COLUMNS}
                        """,
                        params,
                    )
                    row = cur.fetchone()
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise DeviceConflictError(
                    "Já existe dispositivo com este IP ou código de controlador nesta filial."
                ) from exc
            if row is None:
                raise DeviceNotFoundError(str(device_id))
            return dict(row)

    def soft_delete(self, device_id: UUID, *, actor_sub: str | None) -> dict[str, Any]:
        return self.patch(device_id, updates={"enabled": False}, actor_sub=actor_sub)

    def record_poll_success(
        self,
        device_id: UUID,
        *,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.devices
                    SET last_seen_at = NOW(),
                        last_poll_attempt_at = NOW(),
                        last_metrics = %s,
                        last_error = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING {_DEVICE_COLUMNS}
                    """,
                    (Json(metrics), device_id),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise DeviceNotFoundError(str(device_id))
        return dict(row)

    def record_poll_failure(
        self,
        device_id: UUID,
        *,
        error_message: str,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.devices
                    SET last_poll_attempt_at = NOW(),
                        last_error = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING {_DEVICE_COLUMNS}
                    """,
                    (error_message[:2000], device_id),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise DeviceNotFoundError(str(device_id))
        return dict(row)

    def update_next_poll_at(self, device_id: UUID, *, next_poll_at: datetime) -> None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE production_pulse.devices
                    SET next_poll_at = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (next_poll_at, device_id),
                )
            conn.commit()

    def initialize_missing_next_poll_at(self) -> int:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DEVICE_COLUMNS}
                    FROM production_pulse.devices d
                    WHERE d.enabled = TRUE
                      AND d.next_poll_at IS NULL
                      AND EXISTS (
                          SELECT 1
                          FROM production_pulse.device_bindings b
                          WHERE b.device_id = d.id
                            AND b.effective_to IS NULL
                      )
                    """
                )
                rows = list(cur.fetchall())
            conn.commit()

        updated = 0
        for row in rows:
            from production_pulse_app.domain.services.device_poll_schedule_service import (
                compute_initial_poll_at,
            )

            self.update_next_poll_at(
                row["id"],
                next_poll_at=compute_initial_poll_at(int(row["poll_interval_ms"])),
            )
            updated += 1
        return updated

    def list_due_for_scheduled_poll(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DEVICE_COLUMNS}
                    FROM production_pulse.devices d
                    WHERE d.enabled = TRUE
                      AND d.next_poll_at IS NOT NULL
                      AND d.next_poll_at <= NOW()
                      AND EXISTS (
                          SELECT 1
                          FROM production_pulse.device_bindings b
                          WHERE b.device_id = d.id
                            AND b.effective_to IS NULL
                      )
                    ORDER BY d.next_poll_at ASC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return list(cur.fetchall())

    def ensure_next_poll_at(self, device_id: UUID) -> None:
        device = self.get_by_id(device_id)
        if device is None or not device.get("enabled") or device.get("next_poll_at") is not None:
            return
        from production_pulse_app.domain.services.device_poll_schedule_service import (
            compute_initial_poll_at,
        )

        self.update_next_poll_at(
            device_id,
            next_poll_at=compute_initial_poll_at(int(device["poll_interval_ms"])),
        )
