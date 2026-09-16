"""Mapper — status de apontamento HZA → item canônico EN."""

from __future__ import annotations

from typing import Any

from app.domain.services.production.machine_load_operation_mapper import (
    MachineLoadOperationMapper,
)


class MachineLoadAppointmentStatusMapper:
    """Converte linhas agregadas da HZA no mesmo contrato de status da carga máquina."""

    @classmethod
    def map_row(
        cls,
        row: dict[str, Any],
        *,
        order_is_finished: bool = False,
        order_finish_date: str | None = None,
        planned_qty: float | None = None,
        pending_qty: float | None = None,
        operation_produced_qty: float | None = None,
    ) -> dict[str, Any]:
        """Converte a linha da HZA; quantidades da OP e da operação entram como fato.

        A regra de estado é única (``MachineLoadOperationMapper``): OP encerrada
        ou sem saldo nunca fica ``in_progress``, mesmo com apontamento aberto no
        coletor. Quantidades só entram quando vieram do ERP — não inventar 0,
        senão o enrich zeraria o saldo de quem não tem apontamento ainda.
        """
        payload: dict[str, Any] = {
            "branch": row.get("branch"),
            "order_is_finished": 1 if order_is_finished else 0,
            "order_finish_date": order_finish_date,
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
            "active_appointment_count": row.get("active_appointment_count"),
            "active_operator_count": row.get("active_operator_count"),
            "appointment_count": row.get("appointment_count"),
            "last_appointment_date": row.get("last_appointment_date"),
            "active_marker": row.get("active_marker"),
            "last_marker": row.get("last_marker"),
        }
        if planned_qty is not None:
            payload["planned_qty"] = planned_qty
        if pending_qty is not None:
            payload["pending_qty"] = pending_qty
        if operation_produced_qty is not None:
            payload["operation_produced_qty"] = operation_produced_qty
        mapped = MachineLoadOperationMapper.map_operation(payload)
        return {
            "branch": mapped["branch"],
            "production_order": mapped["production_order"],
            "operation_code": mapped["operation_code"],
            "operation_produced_qty": mapped["operation_produced_qty"],
            "operation_pending_qty": mapped["operation_pending_qty"],
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
    def map_rows(
        cls,
        rows: list[dict[str, Any]],
        *,
        finished_by_order: dict[str, dict[str, Any]] | None = None,
        produced_by_operation: dict[tuple[str, str], float] | None = None,
    ) -> list[dict[str, Any]]:
        finished = finished_by_order or {}
        produced = produced_by_operation or {}
        mapped: list[dict[str, Any]] = []
        for row in rows:
            order = str(row.get("production_order") or "").strip()
            operation = str(row.get("operation_code") or "").strip()
            flags = finished.get(order) or {}
            mapped.append(
                cls.map_row(
                    row,
                    order_is_finished=bool(flags.get("is_finished")),
                    order_finish_date=flags.get("finish_date"),
                    planned_qty=flags.get("planned_qty"),
                    pending_qty=flags.get("pending_qty"),
                    operation_produced_qty=produced.get((order, operation)),
                )
            )
        return mapped
