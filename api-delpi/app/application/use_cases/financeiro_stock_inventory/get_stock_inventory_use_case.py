"""Read the R03/P7 operational stock-inventory snapshot (SB9/SB1)."""

from __future__ import annotations

from app.application.dto.financeiro_stock_inventory.constantes import (
    STATUS_AVAILABLE,
    STATUS_INCOMPLETE,
    STATUS_NO_MATCHING_ITEMS,
    STATUS_SOURCE_MISSING,
)
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
            items=[normalize_stock_item(row) for row in rows],
            summariesByType=[normalize_type_summary(row) for row in by_type],
            summariesByWarehouse=[
                normalize_warehouse_summary(row) for row in by_warehouse
            ],
        )
