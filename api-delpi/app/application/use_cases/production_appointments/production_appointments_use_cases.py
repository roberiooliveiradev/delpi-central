from __future__ import annotations

import math
from typing import Any

from app.application.dto.production_appointments.production_appointments_query_request import (
    ProductionAppointmentsQueryRequest,
)
from app.application.services.production.production_operational_summary_service import (
    build_period_summary,
)
from app.domain.ports.production_appointments.production_appointments_repository_port import (
    ProductionAppointmentsRepositoryPort,
)
from app.domain.services.production.production_operational_quantity_service import (
    ProductionOperationalQuantityService,
)


def _calc_total_pages(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return int(math.ceil(total / page_size)) if total > 0 else 0


def _normalize_appointment_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converte qty_* de MI → UN (playbook production_operational_units)."""
    prepared: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        # H6_QTD* é milheiro quando B1_UM está vazio; assume MI.
        if not str(row.get("unit") or "").strip():
            row["unit"] = "MI"
        prepared.append(row)
    return ProductionOperationalQuantityService.normalize_items(prepared)


class ListProductionAppointmentWorkCentersUseCase:
    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        items = self._repository.list_work_centers(branch=request.branch)
        return {
            "branch": request.branch,
            "items": items,
            "summary": {
                "total_records": len(items),
                "branch": request.branch,
                "branch_filter_applied": True,
                "consolidated_across_branches": False,
                "is_complete": True,
            },
        }


class ListProductionAppointmentsUseCase:
    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        date_start, date_end_exclusive = request.protheus_closed_open()
        filters = {
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "work_center": request.work_center,
            "op": request.op,
            "product": request.product,
            "search": request.search,
        }
        items = _normalize_appointment_items(
            self._repository.list_appointments(
                offset=request.offset,
                page_size=request.page_size,
                **filters,
            )
        )
        total = self._repository.count_appointments(**filters)

        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "filters": {
                "work_center": request.work_center,
                "op": request.op,
                "product": request.product,
                "search": request.search,
            },
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=date_start,
                period_end_exclusive=date_end_exclusive,
                is_complete=request.offset + len(items) >= total,
                consolidated_across_branches=False,
            ),
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
                "total_pages": _calc_total_pages(total, request.page_size),
                "is_complete": request.offset + len(items) >= total,
            },
        }


class GetProductionAppointmentsSummaryUseCase:
    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        date_start, date_end_exclusive = request.protheus_closed_open()
        filters = {
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "work_center": request.work_center,
            "op": request.op,
            "product": request.product,
        }
        # Agregações já convertem MI→UN no SQL (fator de production_operational_units).
        by_ct = self._repository.get_summary_by_ct(**filters)
        totals = self._repository.get_summary_totals(**filters)
        display_unit = ProductionOperationalQuantityService.resolve("MI").display_unit or "UN"
        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "filters": {
                "work_center": request.work_center,
                "op": request.op,
                "product": request.product,
            },
            "totals": {
                "appointment_count": int(totals.get("appointment_count") or 0),
                "qty_produced": float(totals.get("qty_produced") or 0),
                "qty_lost": float(totals.get("qty_lost") or 0),
                "op_count": int(totals.get("op_count") or 0),
                "work_center_count": int(totals.get("work_center_count") or 0),
                "unit": display_unit,
            },
            "items": by_ct,
            "summary": build_period_summary(
                items=by_ct,
                branch=request.branch,
                period_start=date_start,
                period_end_exclusive=date_end_exclusive,
                is_complete=True,
                consolidated_across_branches=False,
            ),
        }


class GetProductionAppointmentsSeriesUseCase:
    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        date_start, date_end_exclusive = request.protheus_closed_open()
        points = self._repository.get_series(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
            group_by=request.group_by,
            work_center=request.work_center,
            op=request.op,
            product=request.product,
        )
        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "group_by": request.group_by,
            "filters": {
                "work_center": request.work_center,
                "op": request.op,
                "product": request.product,
            },
            "points": points,
            "summary": build_period_summary(
                items=points,
                branch=request.branch,
                period_start=date_start,
                period_end_exclusive=date_end_exclusive,
                is_complete=True,
                consolidated_across_branches=False,
            ),
        }


class ListProductionAppointmentsByOpUseCase:
    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        date_start, date_end_exclusive = request.protheus_closed_open()
        filters = {
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "work_center": request.work_center,
            "op": request.op,
            "product": request.product,
            "search": request.search,
        }
        items = _normalize_appointment_items(
            self._repository.list_by_op(
                offset=request.offset,
                page_size=request.page_size,
                **filters,
            )
        )
        total = self._repository.count_by_op(**filters)

        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "filters": {
                "work_center": request.work_center,
                "op": request.op,
                "product": request.product,
                "search": request.search,
            },
            "items": items,
            "summary": build_period_summary(
                items=items,
                branch=request.branch,
                period_start=date_start,
                period_end_exclusive=date_end_exclusive,
                is_complete=request.offset + len(items) >= total,
                consolidated_across_branches=False,
            ),
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
                "total_pages": _calc_total_pages(total, request.page_size),
                "is_complete": request.offset + len(items) >= total,
            },
        }
