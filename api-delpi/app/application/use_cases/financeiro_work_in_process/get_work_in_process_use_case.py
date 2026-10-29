"""Read the standalone R08 "Material em Processo" report (MATR989 rule).

One engine, two surfaces: this use case composes the SAME repository
methods the P7 inventory engine consumes — the SB9 process-warehouse
physical slice (MATR989 sem-OP block) plus the SD3 allocated balance
on orders alive at the emission-day cutoff. No second WIP rule.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    STATUS_AVAILABLE,
    STATUS_INCOMPLETE,
    STATUS_NO_MATCHING_ITEMS,
    STATUS_SOURCE_MISSING,
)
from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.dto.financeiro_work_in_process.work_in_process_response import (
    WorkInProcessItem,
    WorkInProcessResponse,
    WorkInProcessTypeSummary,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.application.use_cases.financeiro_stock_inventory.get_stock_inventory_use_case import (
    P7_ENGINE_ID,
    PROCESS_WAREHOUSE,
)
from app.application.use_cases.financeiro_stock_inventory.normalize import (
    as_int,
    build_pagination,
)
from app.domain.ports.financeiro_stock_inventory.stock_inventory_repository_port import (
    StockInventoryRepositoryPort,
)

REPORT_WORK_IN_PROCESS = "work-in-process"
R08_OFFICIAL_PRODUCER = "matr989"

PARITY_NOTE_R08 = (
    "Motor MATR989 reutilizado do motor P7 — composição comprovada "
    "para a competência 09/2026; paridade por competência pendente de "
    "homologação contra nova emissão oficial."
)

_ZERO = Decimal("0")


def _dec_or_none(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _str6(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value.quantize(Decimal("0.000001")))


def _opt(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_item(row: dict) -> WorkInProcessItem:
    qty = _dec_or_none(row.get("allocated_quantity"))
    val = _dec_or_none(row.get("allocated_value"))
    return WorkInProcessItem(
        branchCode=_opt(row.get("branch_code")),
        productCode=str(row.get("product_code") or "").strip(),
        description=_opt(row.get("description")),
        productType=_opt(row.get("product_type")),
        productionOrder=_opt(row.get("production_order")),
        allocatedQuantity=_str6(qty) or "0.000000",
        allocatedValue=_str6(val) or "0.000000",
    )


class GetWorkInProcessUseCase:
    def __init__(
        self,
        repository: StockInventoryRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: StockInventoryQueryRequest,
        *,
        user_subject: str | None,
    ) -> WorkInProcessResponse:
        require_stock_inventory_scope(
            self._scope_resolver, user_subject=user_subject
        )

        snapshot_date = request.reference_date()
        branches = request.requested_branches()
        product_types = request.product_types()

        presence = self._repository.snapshot_branch_counts(
            snapshot_date=snapshot_date, branches=branches
        )
        available = [code for code in branches if presence.get(code, 0) > 0]
        missing = [code for code in branches if code not in available]

        base: dict[str, Any] = {
            "report": REPORT_WORK_IN_PROCESS,
            "period": request.period,
            "referenceDate": request.reference_date_iso(),
            "branchCode": request.branch,
            "reportScope": request.report_scope,
            "branchesAvailable": available,
            "branchesMissing": missing,
        }

        if not available:
            return WorkInProcessResponse(
                **base,
                dataAsOf=None,
                status=STATUS_SOURCE_MISSING,
                physicalTotal=None,
                allocatedTotal=None,
                grandTotal=None,
                pagination=build_pagination(
                    page=request.page,
                    page_size=request.page_size,
                    total_items=0,
                ),
            )

        # Physical block = SB9 rows at the process warehouse — the same
        # "sem-OP" population the P7 engine certifies (doc 80 §41.D).
        physical_by_type = {
            row.get("product_type"): _dec_or_none(
                row.get("total_stock_value")
            )
            or _ZERO
            for row in self._repository.summary_by_type(
                snapshot_date=snapshot_date,
                branches=branches,
                product_types=product_types,
                warehouse=PROCESS_WAREHOUSE,
            )
        }
        wip_by_type = {
            row.get("product_type"): row
            for row in self._repository.work_in_process_by_type(
                branches=branches,
                product_types=product_types,
                movement_cutoff=snapshot_date,
                op_alive_cutoff=request.op_alive_cutoff(),
            )
        }

        type_keys = set(physical_by_type) | set(wip_by_type)
        summaries: list[WorkInProcessTypeSummary] = []
        physical_total = _ZERO
        allocated_total = _ZERO
        for product_type in sorted(
            type_keys, key=lambda t: (t is None, t or "")
        ):
            physical = physical_by_type.get(product_type, _ZERO)
            allocated = _dec_or_none(
                (wip_by_type.get(product_type) or {}).get(
                    "allocated_value"
                )
            ) or _ZERO
            summaries.append(
                WorkInProcessTypeSummary(
                    productType=product_type,
                    physicalValue=_str6(physical) or "0.000000",
                    allocatedValue=_str6(allocated) or "0.000000",
                    totalValue=_str6(physical + allocated) or "0.000000",
                    openOrderCount=as_int(
                        (wip_by_type.get(product_type) or {}).get(
                            "open_order_count"
                        )
                    ),
                )
            )
            physical_total += physical
            allocated_total += allocated

        detail_count = self._repository.work_in_process_detail_count(
            branches=branches,
            product_types=product_types,
            movement_cutoff=snapshot_date,
            op_alive_cutoff=request.op_alive_cutoff(),
        )
        detail_rows = self._repository.work_in_process_detail(
            branches=branches,
            product_types=product_types,
            movement_cutoff=snapshot_date,
            op_alive_cutoff=request.op_alive_cutoff(),
            page=request.page,
            page_size=request.page_size,
        )

        if missing:
            status = STATUS_INCOMPLETE
        elif not summaries:
            status = STATUS_NO_MATCHING_ITEMS
        else:
            status = STATUS_AVAILABLE

        return WorkInProcessResponse(
            **base,
            dataAsOf=request.reference_date_iso(),
            status=status,
            physicalTotal=_str6(physical_total),
            allocatedTotal=_str6(allocated_total),
            grandTotal=_str6(physical_total + allocated_total),
            pagination=build_pagination(
                page=request.page,
                page_size=request.page_size,
                total_items=detail_count,
            ),
            parityStatus=PARITY_STATUS_PENDING,
            parityNotes=[PARITY_NOTE_R08],
            provenance={
                "engine": P7_ENGINE_ID,
                "officialProducer": R08_OFFICIAL_PRODUCER,
                "snapshotDate": request.reference_date_iso(),
                "movementCutoff": request.reference_date_iso(),
                "opAliveCutoff": request.op_alive_cutoff_iso(),
                "processWarehouse": PROCESS_WAREHOUSE,
                "reportScope": request.report_scope,
                "openOrdersAllocated": sum(
                    row.openOrderCount for row in summaries
                ),
                "physicalDetailRef": (
                    "stock-inventory?warehouse=" + PROCESS_WAREHOUSE
                ),
            },
            items=[_normalize_item(row) for row in detail_rows],
            summariesByType=summaries,
        )
