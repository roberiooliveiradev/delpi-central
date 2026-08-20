"""Assembler — payloads de centros de trabalho e fila de operações."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.machine_load_request import (
    MachineLoadFilterRequest,
    MachineLoadOperationsRequest,
)
from app.application.services.paged_list_envelope_service import (
    build_paged_list_envelope,
)
from app.domain.services.production.machine_load_operation_mapper import (
    MachineLoadOperationMapper,
)


class MachineLoadResponseAssembler:
    @staticmethod
    def to_work_centers(
        rows: list[dict[str, Any]],
        request: MachineLoadFilterRequest,
    ) -> dict[str, Any]:
        items = MachineLoadOperationMapper.map_work_centers(rows)
        branch = request.window.branch
        due_dates = [
            value
            for key in ("first_due_date", "last_due_date")
            for item in items
            if (value := item.get(key))
        ]
        return {
            "filters": request.filters_dict(),
            "items": items,
            "summary": {
                "work_center_count": len(items),
                "operation_count": sum(
                    int(item.get("operation_count") or 0) for item in items
                ),
                "order_count": sum(int(item.get("order_count") or 0) for item in items),
                "in_production_count": sum(
                    int(item.get("in_production_count") or 0) for item in items
                ),
                # Entrega mais antiga/mais nova da fila inteira: é o que o PCP usa
                # como início real do período (não existe "de" fixo).
                "first_due_date": min(due_dates) if due_dates else None,
                "last_due_date": max(due_dates) if due_dates else None,
                "missing_due_date_count": sum(
                    int(item.get("missing_due_date_count") or 0) for item in items
                ),
                "branch": branch,
                "branch_filter_applied": branch is not None,
                "consolidated_across_branches": branch is None,
            },
        }

    @staticmethod
    def to_operations(
        rows: list[dict[str, Any]],
        *,
        total: int,
        request: MachineLoadOperationsRequest,
    ) -> dict[str, Any]:
        items = MachineLoadOperationMapper.map_operations(rows)
        return build_paged_list_envelope(
            page=request.page,
            page_size=request.page_size,
            total=total,
            items=items,
            extra={
                "filters": request.filters_dict(),
                "sort": request.sort,
            },
        )
