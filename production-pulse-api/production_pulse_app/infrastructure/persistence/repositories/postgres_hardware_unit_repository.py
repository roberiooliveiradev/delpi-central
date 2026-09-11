from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_UNIT_COLUMNS = """
    id, hardware_uid, current_mac_address, controller_code, hardware_family,
    identity_confidence, identity_source, first_seen_at, last_seen_at,
    created_at, updated_at
"""


class PostgresHardwareUnitRepository:
    def get_by_id(self, unit_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_UNIT_COLUMNS}
                    FROM production_pulse.hardware_units
                    WHERE id = %s
                    """,
                    (unit_id,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def find_by_hardware_uid(self, hardware_uid: str) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_UNIT_COLUMNS}
                    FROM production_pulse.hardware_units
                    WHERE hardware_uid = %s
                    """,
                    (hardware_uid,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def find_by_controller_code(self, controller_code: str) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_UNIT_COLUMNS}
                    FROM production_pulse.hardware_units
                    WHERE controller_code = %s
                    ORDER BY last_seen_at DESC
                    LIMIT 1
                    """,
                    (controller_code,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def find_by_mac(self, mac_address: str) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_UNIT_COLUMNS}
                    FROM production_pulse.hardware_units
                    WHERE current_mac_address = %s
                    ORDER BY last_seen_at DESC
                    LIMIT 1
                    """,
                    (mac_address,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def create(
        self,
        *,
        hardware_uid: str | None,
        mac_address: str | None,
        controller_code: str | None,
        hardware_family: str | None,
        identity_confidence: str,
        identity_source: str,
        seen_at: datetime | None = None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.hardware_units (
                        hardware_uid, current_mac_address, controller_code, hardware_family,
                        identity_confidence, identity_source, first_seen_at, last_seen_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    RETURNING {_UNIT_COLUMNS}
                    """,
                    (
                        hardware_uid,
                        mac_address,
                        controller_code,
                        hardware_family,
                        identity_confidence,
                        identity_source,
                        seen_at,
                        seen_at,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row)

    def touch(
        self,
        unit_id: UUID,
        *,
        mac_address: str | None = None,
        controller_code: str | None = None,
        hardware_uid: str | None = None,
        identity_confidence: str | None = None,
        identity_source: str | None = None,
        seen_at: datetime | None = None,
    ) -> dict[str, Any] | None:
        sets = ["last_seen_at = COALESCE(%s, NOW())", "updated_at = NOW()"]
        params: list[Any] = [seen_at]
        if mac_address is not None:
            sets.append("current_mac_address = %s")
            params.append(mac_address)
        if controller_code is not None:
            sets.append("controller_code = %s")
            params.append(controller_code)
        if hardware_uid is not None:
            sets.append("hardware_uid = COALESCE(hardware_uid, %s)")
            params.append(hardware_uid)
        if identity_confidence is not None:
            sets.append("identity_confidence = %s")
            params.append(identity_confidence)
        if identity_source is not None:
            sets.append("identity_source = %s")
            params.append(identity_source)
        params.append(unit_id)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.hardware_units
                    SET {", ".join(sets)}
                    WHERE id = %s
                    RETURNING {_UNIT_COLUMNS}
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None
