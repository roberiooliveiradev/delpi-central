"""Use cases — carga máquina."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.application.dto.production.machine_load_request import (
    MachineLoadFilterRequest,
    MachineLoadOperationsRequest,
)
from app.application.services.production.machine_load_response_assembler import (
    MachineLoadResponseAssembler,
)
from app.domain.ports.production.machine_load_repository_port import (
    MachineLoadRepositoryPort,
)
from app.domain.services.production.machine_load_appointment_status_mapper import (
    MachineLoadAppointmentStatusMapper,
)
from app.domain.totvs.protheus_operation_appointments import (
    ACTIVE_APPOINTMENT_LOOKBACK_DAYS,
    APPOINTMENT_HISTORY_LOOKBACK_DAYS,
)


class GetProductionMachineLoadWorkCentersUseCase:
    def __init__(self, repository: MachineLoadRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: MachineLoadFilterRequest) -> dict:
        rows = self._repository.get_work_centers(**request.filter_kwargs())
        return MachineLoadResponseAssembler.to_work_centers(rows, request)


class GetProductionMachineLoadOperationsUseCase:
    def __init__(self, repository: MachineLoadRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: MachineLoadOperationsRequest) -> dict:
        filters = request.filter_kwargs()
        total = self._repository.count_operations(**filters)
        rows = self._repository.get_operations(
            **filters,
            sort=request.sort,
            offset=request.offset,
            page_size=request.page_size,
        )
        return MachineLoadResponseAssembler.to_operations(
            rows, total=total, request=request
        )


class GetProductionMachineLoadAppointmentStatusUseCase:
    """Status HZA vivo para enriquecer snapshot congelado no BFF PCP."""

    def __init__(self, repository: MachineLoadRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        items: list[dict[str, Any]],
        today: date | None = None,
    ) -> dict:
        reference = today or date.today()
        active_since = (
            reference - timedelta(days=ACTIVE_APPOINTMENT_LOOKBACK_DAYS)
        ).strftime("%Y%m%d")
        history_since = (
            reference - timedelta(days=APPOINTMENT_HISTORY_LOOKBACK_DAYS)
        ).strftime("%Y%m%d")

        rows = self._repository.get_appointment_status(
            branch=branch,
            appointment_active_since=active_since,
            appointment_history_since=history_since,
        )

        wanted: list[tuple[str, str]] = []
        for raw in items:
            order = str(raw.get("production_order") or "").strip()
            operation = str(raw.get("operation_code") or "").strip()
            if order and operation:
                wanted.append((order, operation))

        # Sem lista explícita: devolve o agregado da filial (útil em testes).
        keys = wanted or [
            (
                str(row.get("production_order") or "").strip(),
                str(row.get("operation_code") or "").strip(),
            )
            for row in rows
        ]
        order_codes = sorted({order for order, _operation in keys if order})
        # O encerramento entra antes do mapeamento: é ele que derruba o
        # apontamento aberto que o operador esqueceu no coletor.
        finished_by_order = self._finished_orders_by_code(
            branch=branch, production_orders=order_codes
        )

        mapped = MachineLoadAppointmentStatusMapper.map_rows(
            rows, finished_by_order=finished_by_order
        )
        by_key = {
            (item["production_order"], item["operation_code"]): item for item in mapped
        }

        result_items: list[dict] = []
        for order, operation in keys:
            hit = by_key.get((order, operation))
            if hit is not None:
                result_items.append(dict(hit))
                continue
            finish = finished_by_order.get(order)
            result_items.append(
                MachineLoadAppointmentStatusMapper.map_row(
                    {
                        "branch": branch,
                        "production_order": order,
                        "operation_code": operation,
                    },
                    order_is_finished=finish is not None,
                    order_finish_date=(finish or {}).get("finish_date"),
                )
            )

        return {
            "branch": branch,
            "items": result_items,
            "summary": {
                "requested_count": len(keys),
                "in_production_count": sum(
                    1 for item in result_items if item.get("is_in_production")
                ),
            },
        }

    def _finished_orders_by_code(
        self, *, branch: str, production_orders: list[str]
    ) -> dict[str, dict[str, Any]]:
        if not production_orders or not hasattr(
            self._repository, "get_order_finish_flags"
        ):
            return {}
        rows = self._repository.get_order_finish_flags(
            branch=branch, production_orders=production_orders
        )
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            order = str(row.get("production_order") or "").strip()
            if not order:
                continue
            is_finished = int(float(row.get("is_finished") or 0)) > 0
            if not is_finished:
                continue
            finish_raw = row.get("finish_date")
            finish_date = None
            if finish_raw is not None and str(finish_raw).strip():
                text = str(finish_raw).strip()
                if text.isdigit() and len(text) == 8:
                    finish_date = f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
                else:
                    finish_date = text[:10]
            out[order] = {"finish_date": finish_date}
        return out
