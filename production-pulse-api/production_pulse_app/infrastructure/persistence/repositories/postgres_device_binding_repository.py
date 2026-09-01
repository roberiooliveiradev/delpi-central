from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.domain.services.binding_validation_service import NormalizedBindingInput
from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import plugins_connection


_BINDING_COLUMNS = """
    id, device_id, anchor_type, placement_label, placement_key,
    work_center_code, work_center_name, machine_code, machine_label,
    equipment_label, area_label, resource_code, tool_code, notes,
    effective_from, effective_to, created_at, updated_at, created_by, updated_by
"""


class BindingNotFoundError(Exception):
    pass


class PostgresDeviceBindingRepository:
    def get_active(self, device_id: UUID) -> dict[str, Any] | None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_BINDING_COLUMNS}
                    FROM production_pulse.device_bindings
                    WHERE device_id = %s AND effective_to IS NULL
                    LIMIT 1
                    """,
                    (device_id,),
                )
                return cur.fetchone()

    def placement_key_exists(self, placement_key: str, *, exclude_device_id: UUID | None = None) -> bool:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                if exclude_device_id:
                    cur.execute(
                        """
                        SELECT 1 FROM production_pulse.device_bindings
                        WHERE placement_key = %s
                          AND effective_to IS NULL
                          AND device_id <> %s
                        LIMIT 1
                        """,
                        (placement_key, exclude_device_id),
                    )
                else:
                    cur.execute(
                        """
                        SELECT 1 FROM production_pulse.device_bindings
                        WHERE placement_key = %s AND effective_to IS NULL
                        LIMIT 1
                        """,
                        (placement_key,),
                    )
                return cur.fetchone() is not None

    def active_device_ids_among(self, device_ids: list[UUID]) -> set[UUID]:
        if not device_ids:
            return set()
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT device_id
                    FROM production_pulse.device_bindings
                    WHERE device_id = ANY(%s::uuid[])
                      AND effective_to IS NULL
                    """,
                    (device_ids,),
                )
                return {row["device_id"] for row in cur.fetchall()}

    def resolve_unique_placement_key(self, base_key: str, device_id: UUID) -> str:
        # Vários devices podem compartilhar a mesma âncora (mesmo placement_key).
        # Colisão de slug entre rótulos distintos fica para evolução futura (E5+).
        return base_key

    def close_active(self, device_id: UUID, *, actor_sub: str | None) -> None:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE production_pulse.device_bindings
                    SET effective_to = NOW(),
                        updated_by = %s,
                        updated_at = NOW()
                    WHERE device_id = %s AND effective_to IS NULL
                    """,
                    (actor_sub, device_id),
                )
            conn.commit()

    def create(
        self,
        device_id: UUID,
        binding: NormalizedBindingInput,
        *,
        placement_label: str,
        placement_key: str,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO production_pulse.device_bindings (
                        device_id, anchor_type, placement_label, placement_key,
                        work_center_code, work_center_name, machine_code, machine_label,
                        equipment_label, area_label, resource_code, tool_code, notes,
                        created_by, updated_by
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s
                    )
                    RETURNING {_BINDING_COLUMNS}
                    """,
                    (
                        device_id,
                        binding.anchor_type,
                        placement_label,
                        placement_key,
                        binding.work_center_code,
                        binding.work_center_name,
                        binding.machine_code,
                        binding.machine_label,
                        binding.equipment_label,
                        binding.area_label,
                        binding.resource_code,
                        binding.tool_code,
                        binding.notes,
                        actor_sub,
                        actor_sub,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row)

    def list_history(
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
                    FROM production_pulse.device_bindings
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    f"""
                    SELECT {_BINDING_COLUMNS}
                    FROM production_pulse.device_bindings
                    WHERE device_id = %s
                    ORDER BY effective_from DESC, created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (device_id, page_size, offset),
                )
                rows = list(cur.fetchall())
        return rows, total
