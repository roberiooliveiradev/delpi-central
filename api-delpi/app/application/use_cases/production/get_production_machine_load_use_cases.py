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
    PRODUCTION_STATUS_NOT_STARTED,
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
        mapped = MachineLoadAppointmentStatusMapper.map_rows(rows)
        by_key = {
            (item["production_order"], item["operation_code"]): item for item in mapped
        }

        wanted: list[tuple[str, str]] = []
        for raw in items:
            order = str(raw.get("production_order") or "").strip()
            operation = str(raw.get("operation_code") or "").strip()
            if order and operation:
                wanted.append((order, operation))

        # Sem lista explícita: devolve o agregado da filial (útil em testes).
        keys = wanted or list(by_key.keys())
        result_items: list[dict] = []
        for order, operation in keys:
            hit = by_key.get((order, operation))
            if hit is not None:
                result_items.append(hit)
            else:
                result_items.append(
                    {
                        "branch": branch,
                        "production_order": order,
                        "operation_code": operation,
                        "production_status": PRODUCTION_STATUS_NOT_STARTED,
                        "is_in_production": False,
                        "production_started_date": None,
                        "production_started_time": None,
                        "active_operator_code": None,
                        "active_operator_name": None,
                        "active_operator_count": 0,
                        "appointment_count": 0,
                        "last_appointment_date": None,
                    }
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
