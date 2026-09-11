from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_COLUMNS = """
    driver_key, protocol_kind, role_key, label_pt, description_pt,
    metrics, commands, operator_surface, operator_eligible,
    poll, thresholds, counter_restore, archived_at, created_at, updated_at
"""

PROTOCOL_KINDS = frozenset({"http_counter", "http_gauge"})


class DeviceDriverConflictError(Exception):
    pass


class DeviceDriverNotFoundError(Exception):
    pass


class PostgresDeviceDriverRepository:
    def list_drivers(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        if not include_archived:
            clauses.append("archived_at IS NULL")
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_COLUMNS}
                    FROM production_pulse.device_drivers
                    WHERE {" AND ".join(clauses)}
                    ORDER BY driver_key
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def get_by_key(self, driver_key: str) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_COLUMNS}
                    FROM production_pulse.device_drivers
                    WHERE driver_key = %s
                    """,
                    (driver_key,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM production_pulse.device_drivers WHERE driver_key = %s",
                    (payload["driver_key"],),
                )
                if cur.fetchone():
                    raise DeviceDriverConflictError("driverKeyExists")
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.device_drivers (
                        driver_key, protocol_kind, role_key, label_pt, description_pt,
                        metrics, commands, operator_surface, operator_eligible,
                        poll, thresholds, counter_restore
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING {_COLUMNS}
                    """,
                    (
                        payload["driver_key"],
                        payload["protocol_kind"],
                        payload["role_key"],
                        payload["label_pt"],
                        payload.get("description_pt"),
                        Json(payload.get("metrics") or []),
                        Json(payload.get("commands") or []),
                        payload["operator_surface"],
                        bool(payload.get("operator_eligible", True)),
                        Json(payload.get("poll") or {"timeoutMs": 3000}),
                        Json(payload.get("thresholds") or {}),
                        Json(payload["counter_restore"])
                        if payload.get("counter_restore") is not None
                        else None,
                    ),
                )
                row = dict(cur.fetchone())
            conn.commit()
            return row

    def update(self, driver_key: str, updates: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "role_key": "role_key",
            "label_pt": "label_pt",
            "description_pt": "description_pt",
            "metrics": "metrics",
            "commands": "commands",
            "operator_surface": "operator_surface",
            "operator_eligible": "operator_eligible",
            "poll": "poll",
            "thresholds": "thresholds",
            "counter_restore": "counter_restore",
        }
        sets: list[str] = []
        params: list[Any] = []
        for api_key, column in allowed.items():
            if api_key not in updates:
                continue
            value = updates[api_key]
            if column in {"metrics", "commands", "poll", "thresholds", "counter_restore"}:
                sets.append(f"{column} = %s")
                params.append(Json(value) if value is not None else None)
            else:
                sets.append(f"{column} = %s")
                params.append(value)
        if not sets:
            existing = self.get_by_key(driver_key)
            if existing is None:
                raise DeviceDriverNotFoundError(driver_key)
            return existing
        sets.append("updated_at = NOW()")
        params.append(driver_key)
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_drivers
                    SET {", ".join(sets)}
                    WHERE driver_key = %s
                    RETURNING {_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
                if row is None:
                    raise DeviceDriverNotFoundError(driver_key)
            conn.commit()
            return dict(row)

    def archive(self, driver_key: str) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_drivers
                    SET archived_at = COALESCE(archived_at, NOW()), updated_at = NOW()
                    WHERE driver_key = %s
                    RETURNING {_COLUMNS}
                    """,
                    (driver_key,),
                )
                row = cur.fetchone()
                if row is None:
                    raise DeviceDriverNotFoundError(driver_key)
            conn.commit()
            return dict(row)

    def unarchive(self, driver_key: str) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE production_pulse.device_drivers
                    SET archived_at = NULL, updated_at = NOW()
                    WHERE driver_key = %s
                    RETURNING {_COLUMNS}
                    """,
                    (driver_key,),
                )
                row = cur.fetchone()
                if row is None:
                    raise DeviceDriverNotFoundError(driver_key)
            conn.commit()
            return dict(row)

    def count_device_refs(self, driver_key: str) -> int:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM production_pulse.devices
                    WHERE driver_key = %s
                    """,
                    (driver_key,),
                )
                return int(cur.fetchone()["n"] or 0)

    def count_firmware_refs(self, driver_key: str) -> int:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM production_pulse.firmwares
                    WHERE driver_key = %s
                    """,
                    (driver_key,),
                )
                return int(cur.fetchone()["n"] or 0)

    def hard_delete(self, driver_key: str) -> bool:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM production_pulse.device_drivers
                    WHERE driver_key = %s
                    RETURNING driver_key
                    """,
                    (driver_key,),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None
