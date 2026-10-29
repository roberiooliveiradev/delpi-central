"""Read the R03/P7 operational stock-inventory snapshot (SB9/SB1)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_NOTE_ALL_PRODUCTS,
    PARITY_NOTE_MP_PI_PA,
    PARITY_STATUS_PENDING,
    REPORT_SCOPE_MP_PI_PA,
    STATUS_AVAILABLE,
    STATUS_INCOMPLETE,
    STATUS_NO_MATCHING_ITEMS,
    STATUS_SOURCE_MISSING,
)
from app.domain.totvs.protheus_warehouses import WAREHOUSE_FABRICA
from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.dto.financeiro_stock_inventory.stock_inventory_response import (
    StockInventoryResponse,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.financeiro_stock_inventory.stock_inventory_repository_port import (
    StockInventoryRepositoryPort,
)

from .normalize import (
    as_int,
    build_pagination,
    normalize_stock_item,
    normalize_type_summary,
    normalize_warehouse_summary,
)

REPORT_STOCK_INVENTORY = "stock-inventory"

# Process warehouse for the official P7 split — ``B9_LOCAL = '99'``
# (MV_LOCPROC / factory WIP) is the physical slice of EM PROCESSO; the
# allocated slice is the MATR989 RE*−DE* balance on OPs alive at the
# emission-day cutoff (doc 80 §41).
PROCESS_WAREHOUSE = WAREHOUSE_FABRICA

P7_ENGINE_ID = "minha-delpi-p7-inventory-engine"
P7_OFFICIAL_PRODUCER = "matr460"


def _decimal_or_none(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value.quantize(Decimal("0.000001")))


def _parity_notes(report_scope: str) -> list[str]:
    if report_scope == REPORT_SCOPE_MP_PI_PA:
        return [PARITY_NOTE_ALL_PRODUCTS, PARITY_NOTE_MP_PI_PA]
    return [PARITY_NOTE_ALL_PRODUCTS]


class GetStockInventoryUseCase:
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
    ) -> StockInventoryResponse:
        # Fail-closed: real rows only when the dataset scope is proven
        # authorized (doc 49 §8). Unresolved scope raises
        # StockInventoryScopeUnavailableError -> typed 403 at the route layer.
        require_stock_inventory_scope(self._scope_resolver, user_subject=user_subject)

        snapshot_date = request.reference_date()
        requested = request.requested_branches()

        # Snapshot presence is checked WITHOUT functional filters, so a
        # missing SB9 snapshot can never masquerade as an empty result.
        presence = self._repository.snapshot_branch_counts(
            snapshot_date=snapshot_date, branches=requested
        )
        available = [code for code in requested if presence.get(code, 0) > 0]
        missing = [code for code in requested if code not in available]

        base = {
            "report": REPORT_STOCK_INVENTORY,
            "period": request.period,
            "referenceDate": request.reference_date_iso(),
            "branchCode": request.branch,
            "reportScope": request.report_scope,
            "branchesAvailable": available,
            "branchesMissing": missing,
        }

        if not available:
            # EXECUTION_DRIFT case (e.g. SB9 2026-09 filial 01): no snapshot
            # -> explicit source_missing, never a fabricated 0.00 total.
            return StockInventoryResponse(
                **base,
                dataAsOf=None,
                status=STATUS_SOURCE_MISSING,
                historicalTotal=None,
                pagination=build_pagination(
                    page=request.page,
                    page_size=request.page_size,
                    total_items=0,
                ),
            )

        product_types = request.product_types()
        totals = self._repository.totals(
            snapshot_date=snapshot_date,
            branches=requested,
            product_types=product_types,
            warehouse=request.warehouse,
        )
        total_items = as_int(totals.get("item_count"))

        rows = self._repository.list_items(
            snapshot_date=snapshot_date,
            branches=requested,
            product_types=product_types,
            warehouse=request.warehouse,
            page=request.page,
            page_size=request.page_size,
        )
        by_type = self._repository.summary_by_type(
            snapshot_date=snapshot_date,
            branches=requested,
            product_types=product_types,
            warehouse=request.warehouse,
        )
        by_warehouse = self._repository.summary_by_warehouse(
            snapshot_date=snapshot_date,
            branches=requested,
            product_types=product_types,
            warehouse=request.warehouse,
        )

        if missing:
            status = STATUS_INCOMPLETE
        elif total_items == 0:
            # Snapshot exists but filters matched nothing — legitimate empty.
            status = STATUS_NO_MATCHING_ITEMS
        else:
            status = STATUS_AVAILABLE

        # Official P7 composition on the scope universe (doc 80 §41 /
        # doc 119 §8): EM ESTOQUE (SB9 ex-process warehouse) + EM PROCESSO
        # (physical warehouse-99 slice + MATR989 allocated WIP on OPs
        # alive at the emission-day cutoff). Report-level totalizers —
        # the ``warehouse`` item filter never narrows them.
        p7 = self._repository.p7_totals(
            snapshot_date=snapshot_date,
            branches=requested,
            product_types=product_types,
            process_warehouse=PROCESS_WAREHOUSE,
        )
        wip_rows = self._repository.work_in_process_by_type(
            branches=requested,
            product_types=product_types,
            movement_cutoff=snapshot_date,
            op_alive_cutoff=request.op_alive_cutoff(),
        )
        stock_total = _decimal_or_none(p7.get("stock_value"))
        process_physical = _decimal_or_none(p7.get("process_physical_value"))
        process_allocated = sum(
            (
                _decimal_or_none(row.get("allocated_value")) or Decimal("0")
                for row in wip_rows
            ),
            Decimal("0"),
        )
        process_total = (
            None
            if process_physical is None
            else process_physical + process_allocated
        )
        # TOTAL is certified only when BOTH parcels are known — a missing
        # WIP measure is never masked as zero inside the grand total.
        grand_total = (
            None
            if stock_total is None or process_total is None
            else stock_total + process_total
        )

        total_value = totals.get("total_value")
        return StockInventoryResponse(
            **base,
            dataAsOf=request.reference_date_iso(),
            status=status,
            historicalTotal=None if total_value is None else str(total_value),
            pagination=build_pagination(
                page=request.page,
                page_size=request.page_size,
                total_items=total_items,
            ),
            stockTotal=_decimal_str(stock_total),
            processPhysicalTotal=_decimal_str(process_physical),
            processAllocatedTotal=_decimal_str(process_allocated),
            processTotal=_decimal_str(process_total),
            grandTotal=_decimal_str(grand_total),
            parityStatus=PARITY_STATUS_PENDING,
            parityNotes=_parity_notes(request.report_scope),
            provenance={
                "engine": P7_ENGINE_ID,
                "officialProducer": P7_OFFICIAL_PRODUCER,
                "snapshotDate": request.reference_date_iso(),
                "movementCutoff": request.reference_date_iso(),
                "opAliveCutoff": request.op_alive_cutoff_iso(),
                "processWarehouse": PROCESS_WAREHOUSE,
                "reportScope": request.report_scope,
                "openOrdersAllocated": sum(
                    as_int(row.get("open_order_count")) for row in wip_rows
                ),
            },
            items=[normalize_stock_item(row) for row in rows],
            summariesByType=[normalize_type_summary(row) for row in by_type],
            summariesByWarehouse=[
                normalize_warehouse_summary(row) for row in by_warehouse
            ],
        )
