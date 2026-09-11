from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_ASSIGNMENT_COLUMNS = """
    id, device_id, hardware_unit_id, effective_from, effective_to,
    ip_address_snapshot, mac_address_snapshot, controller_code_snapshot, hardware_uid_snapshot,
    identity_confidence, replacement_reason, replacement_notes,
    first_firmware_version, last_firmware_version,
    first_counter_raw, last_counter_raw, logical_counter_at_start, logical_counter_at_end,
    counter_delta_total, online_seconds_total, reboot_count,
    last_seen_at, last_uptime_ms, last_success_poll_at,
    created_at, updated_at, created_by, updated_by
"""


class PostgresDeviceHardwareAssignmentRepository:
    def get_active_for_device(self, device_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ASSIGNMENT_COLUMNS}
                    FROM production_pulse.device_hardware_assignments
                    WHERE device_id = %s AND effective_to IS NULL
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def get_active_for_unit(self, hardware_unit_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ASSIGNMENT_COLUMNS}
                    FROM production_pulse.device_hardware_assignments
                    WHERE hardware_unit_id = %s AND effective_to IS NULL
                    """,
                    (hardware_unit_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def get_by_id(self, assignment_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ASSIGNMENT_COLUMNS}
                    FROM production_pulse.device_hardware_assignments
                    WHERE id = %s
                    """,
                    (assignment_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def list_for_device(self, device_id: UUID) -> list[dict[str, Any]]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ASSIGNMENT_COLUMNS}
                    FROM production_pulse.device_hardware_assignments
                    WHERE device_id = %s
                    ORDER BY effective_from DESC, created_at DESC
                    """,
                    (device_id,),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def open_assignment(
        self,
        *,
        device_id: UUID,
        hardware_unit_id: UUID,
        ip_address: str | None,
        mac_address: str | None,
        controller_code: str | None,
        hardware_uid: str | None,
        identity_confidence: str,
        firmware_version: str | None,
        counter_raw: int | None,
        logical_counter: int | None,
        actor_sub: str | None = None,
        effective_from: datetime | None = None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.device_hardware_assignments (
                        device_id, hardware_unit_id, effective_from,
                        ip_address_snapshot, mac_address_snapshot, controller_code_snapshot,
                        hardware_uid_snapshot, identity_confidence,
                        first_firmware_version, last_firmware_version,
                        first_counter_raw, last_counter_raw,
                        logical_counter_at_start,
                        last_seen_at, last_success_poll_at, created_by, updated_by
                    )
                    VALUES (
                        %s, %s, COALESCE(%s, NOW()),
                        %s::inet, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s,
                        NOW(), NOW(), %s, %s
                    )
                    RETURNING {_ASSIGNMENT_COLUMNS}
                    """,
                    (
                        device_id,
                        hardware_unit_id,
                        effective_from,
                        ip_address,
                        mac_address,
                        controller_code,
                        hardware_uid,
                        identity_confidence,
                        firmware_version,
                        firmware_version,
                        counter_raw,
                        counter_raw,
                        logical_counter,
                        actor_sub,
                        actor_sub,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def close_assignment(
        self,
        assignment_id: UUID,
        *,
        logical_counter_at_end: int | None = None,
        last_counter_raw: int | None = None,
        last_firmware_version: str | None = None,
        closed_at: datetime | None = None,
        actor_sub: str | None = None,
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_hardware_assignments
                    SET effective_to = COALESCE(%s, NOW()),
                        logical_counter_at_end = COALESCE(%s, logical_counter_at_end),
                        last_counter_raw = COALESCE(%s, last_counter_raw),
                        last_firmware_version = COALESCE(%s, last_firmware_version),
                        updated_at = NOW(),
                        updated_by = COALESCE(%s, updated_by)
                    WHERE id = %s AND effective_to IS NULL
                    RETURNING {_ASSIGNMENT_COLUMNS}
                    """,
                    (
                        closed_at,
                        logical_counter_at_end,
                        last_counter_raw,
                        last_firmware_version,
                        actor_sub,
                        assignment_id,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def update_poll_stats(
        self,
        assignment_id: UUID,
        *,
        counter_raw: int | None,
        counter_delta: int,
        firmware_version: str | None,
        online_seconds_add: int,
        reboot_increment: int,
        uptime_ms: int | None,
        mac_address: str | None = None,
        controller_code: str | None = None,
        success_at: datetime | None = None,
    ) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_hardware_assignments
                    SET last_counter_raw = COALESCE(%s, last_counter_raw),
                        counter_delta_total = counter_delta_total + GREATEST(0, %s),
                        last_firmware_version = COALESCE(%s, last_firmware_version),
                        online_seconds_total = online_seconds_total + GREATEST(0, %s),
                        reboot_count = reboot_count + GREATEST(0, %s),
                        last_uptime_ms = COALESCE(%s, last_uptime_ms),
                        mac_address_snapshot = COALESCE(%s, mac_address_snapshot),
                        controller_code_snapshot = COALESCE(%s, controller_code_snapshot),
                        last_seen_at = NOW(),
                        last_success_poll_at = COALESCE(%s, NOW()),
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING {_ASSIGNMENT_COLUMNS}
                    """,
                    (
                        counter_raw,
                        int(counter_delta),
                        firmware_version,
                        int(online_seconds_add),
                        int(reboot_increment),
                        uptime_ms,
                        mac_address,
                        controller_code,
                        success_at,
                        assignment_id,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def patch_metadata(
        self,
        assignment_id: UUID,
        *,
        replacement_reason: str | None = None,
        replacement_notes: str | None = None,
        actor_sub: str | None = None,
    ) -> dict[str, Any] | None:
        sets: list[str] = ["updated_at = NOW()"]
        params: list[Any] = []
        if replacement_reason is not None:
            sets.append("replacement_reason = %s")
            params.append(replacement_reason)
        if replacement_notes is not None:
            sets.append("replacement_notes = %s")
            params.append(replacement_notes)
        if actor_sub is not None:
            sets.append("updated_by = %s")
            params.append(actor_sub)
        params.append(assignment_id)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_hardware_assignments
                    SET {", ".join(sets)}
                    WHERE id = %s
                    RETURNING {_ASSIGNMENT_COLUMNS}
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def insert_event(
        self,
        *,
        device_id: UUID,
        event_type: str,
        assignment_id: UUID | None = None,
        hardware_unit_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
        actor_sub: str | None = None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO production_pulse.device_hardware_events (
                        device_id, assignment_id, hardware_unit_id, event_type, payload, created_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, device_id, assignment_id, hardware_unit_id, event_type, payload, created_at, created_by
                    """,
                    (
                        device_id,
                        assignment_id,
                        hardware_unit_id,
                        event_type,
                        Json(payload or {}),
                        actor_sub,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def list_events(self, device_id: UUID, *, limit: int = 50) -> list[dict[str, Any]]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, device_id, assignment_id, hardware_unit_id, event_type, payload, created_at, created_by
                    FROM production_pulse.device_hardware_events
                    WHERE device_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (device_id, limit),
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]

    def count_for_device(self, device_id: UUID) -> dict[str, int]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      COUNT(*) AS assignments,
                      COUNT(*) FILTER (WHERE effective_to IS NOT NULL) AS replacements,
                      COUNT(DISTINCT hardware_unit_id) AS hardware_units,
                      COUNT(DISTINCT mac_address_snapshot)
                        FILTER (WHERE mac_address_snapshot IS NOT NULL) AS macs
                    FROM production_pulse.device_hardware_assignments
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        return {
            "assignments": int(row["assignments"] or 0),
            "replacements": int(row["replacements"] or 0),
            "hardwareUnits": int(row["hardware_units"] or 0),
            "macs": int(row["macs"] or 0),
        }

    def count_events_for_device(self, device_id: UUID) -> int:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM production_pulse.device_hardware_events
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        return int(row["total"] or 0)

    def sum_legacy_counter_before_traceability(self, device_id: UUID) -> int:
        """Sum of counter deltas from readings without hardware assignment."""
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(SUM((delta_metrics->>'counter')::bigint), 0) AS total
                    FROM production_pulse.readings
                    WHERE device_id = %s
                      AND hardware_assignment_id IS NULL
                      AND delta_metrics ? 'counter'
                    """,
                    (device_id,),
                )
                row = cur.fetchone()
        return int(row["total"] or 0)
