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
from app.domain.services.production.production_appointments_op_family_service import (
    ProductionAppointmentsOpFamilyService,
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
            "mother_op": request.mother_op,
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
                "mother_op": request.mother_op,
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
            "mother_op": request.mother_op,
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
                "mother_op": request.mother_op,
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
            granularity=request.granularity,
            work_center=request.work_center,
            op=request.op,
            product=request.product,
            mother_op=request.mother_op,
        )
        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "group_by": request.group_by,
            "granularity": request.granularity,
            "filters": {
                "work_center": request.work_center,
                "op": request.op,
                "product": request.product,
                "mother_op": request.mother_op,
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
            "mother_op": request.mother_op,
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
                "mother_op": request.mother_op,
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


class ListProductionAppointmentsChildOpsUseCase:
    """OPs filhas da mesma família (prefixo antes da sequência; sufixo ≠ 001)."""

    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductionAppointmentsQueryRequest) -> dict:
        reference_op = ProductionAppointmentsOpFamilyService.normalize_op(request.op)
        if not reference_op:
            raise ValueError("op é obrigatório para listar OPs filhas.")

        family_prefix = ProductionAppointmentsOpFamilyService.family_prefix(reference_op)
        date_start, date_end_exclusive = request.protheus_closed_open()
        filters = {
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": request.branch,
            "work_center": request.work_center,
            "product": request.product,
            "search": request.search,
            "op_family_prefix": family_prefix,
            "child_ops_only": True,
            "exclude_op": reference_op,
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
            "reference_op": reference_op,
            "family_prefix": family_prefix,
            "filters": {
                "work_center": request.work_center,
                "op": reference_op,
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


class GetProductionAppointmentsFinishedOpsSeriesUseCase:
    """Série de quantidade de OPs finalizadas (SC2.C2_DATRF) por dia ou mês."""

    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(self, request) -> dict:
        date_start, date_end_exclusive = request.protheus_closed_open()
        rows = self._repository.get_finished_ops_series(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
            granularity=request.granularity,
            product=request.product,
            mother_op=request.mother_op,
        )
        points = [
            {
                "bucket": str(row.get("bucket") or "").strip(),
                "periodo": _bucket_to_periodo(
                    str(row.get("bucket") or "").strip(),
                    request.granularity,
                ),
                "ops_finished_count": int(row.get("ops_finished_count") or 0),
            }
            for row in rows
        ]
        total_ops = sum(point["ops_finished_count"] for point in points)
        return {
            "period": {"start": date_start, "end_exclusive": date_end_exclusive},
            "branch": request.branch,
            "granularity": request.granularity,
            "filters": {
                "product": request.product,
                "mother_op": request.mother_op,
            },
            "totals": {"ops_finished_count": total_ops},
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


def _bucket_to_periodo(bucket: str, granularity: str) -> str:
    raw = str(bucket or "").strip()
    if granularity == "month" and len(raw) >= 6:
        return f"{raw[:4]}-{raw[4:6]}"
    if len(raw) >= 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw
