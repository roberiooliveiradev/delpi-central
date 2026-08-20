"""Mapper — status de apontamento HZA → item canônico EN."""

from __future__ import annotations

from typing import Any

from app.domain.services.production.machine_load_operation_mapper import (
    MachineLoadOperationMapper,
)


class MachineLoadAppointmentStatusMapper:
    """Converte linhas agregadas da HZA no mesmo contrato de status da carga máquina."""

    @classmethod
    def map_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        mapped = MachineLoadOperationMapper.map_operation(
            {
                "branch": row.get("branch"),
                "work_center": "",
                "work_center_name": "",
                "scheduled_date": None,
                "scheduled_start_time": None,
                "production_order": row.get("production_order"),
                "operation_code": row.get("operation_code"),
                "operation_description": "",
                "tool": "",
                "product_code": "",
                "product_description": "",
                "planned_qty": 0,
                "produced_qty": 0,
                "pending_qty": 0,
                "active_appointment_count": row.get("active_appointment_count"),
                "active_operator_count": row.get("active_operator_count"),
                "appointment_count": row.get("appointment_count"),
                "last_appointment_date": row.get("last_appointment_date"),
                "active_marker": row.get("active_marker"),
                "last_marker": row.get("last_marker"),
            }
        )
        return {
            "branch": mapped["branch"],
            "production_order": mapped["production_order"],
            "operation_code": mapped["operation_code"],
            "production_status": mapped["production_status"],
            "is_in_production": mapped["is_in_production"],
            "production_started_date": mapped["production_started_date"],
            "production_started_time": mapped["production_started_time"],
            "active_operator_code": mapped["active_operator_code"],
            "active_operator_name": mapped["active_operator_name"],
            "active_operator_count": mapped["active_operator_count"],
            "appointment_count": mapped["appointment_count"],
            "last_appointment_date": mapped["last_appointment_date"],
        }

    @classmethod
    def map_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.map_row(row) for row in rows]
