"""Read the R06 stock-kardex movement list (MATR910, doc 122 §4).

Returns the paginated movement lines (artifact grain), the product
blocks of the products present on the page, and the global totals —
every aggregate covers the full authorized universe, not the page.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    PARITY_STATUS_TEST_NOT_RUN,
    STATUS_SOURCE_MISSING,
)
from app.application.dto.financeiro_stock_kardex.constantes import (
    DOCUMENT_KIND_INVENT,
    MOVEMENT_KIND_ENTRY,
    MOVEMENT_KIND_OUTPUT,
    SORT_FIELD_PRODUCT,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_response import (
    StockKardexBlock,
    StockKardexMovement,
    StockKardexResponse,
    StockKardexTotals,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
)
from app.domain.ports.financeiro_stock_kardex.stock_kardex_repository_port import (
    StockKardexRepositoryPort,
)

from ._engine import (
    PARITY_NOTE_R06,
    PARITY_NOTE_R07,
    R06_ENGINE_ID,
    R06_OFFICIAL_PRODUCER,
    KardexUniverse,
    ProcessedMovement,
    build_reference,
    load_kardex_universe,
    report_name,
    str6,
)


def _sort_key(movement: ProcessedMovement, sort: str):
    row = movement.raw
    date_key = (
        str(row.get("movement_date") or ""),
        str(row.get("sequence_number") or ""),
        int(row.get("movement_id") or 0),
    )
    if sort == SORT_FIELD_PRODUCT:
        return (
            str(row.get("product_code") or ""),
            str(row.get("warehouse") or ""),
            *date_key,
        )
    return (
        *date_key,
        str(row.get("product_code") or ""),
        str(row.get("warehouse") or ""),
    )


def _movement_dto(movement: ProcessedMovement) -> StockKardexMovement:
    row = movement.raw
    return StockKardexMovement(
        sourceTable=str(row.get("source_table") or ""),
        movementId=int(row.get("movement_id") or 0),
        branchCode=str(row.get("branch_code") or ""),
        warehouse=str(row.get("warehouse") or ""),
        productCode=str(row.get("product_code") or ""),
        description=row.get("description"),
        productType=row.get("product_type"),
        unit=row.get("unit"),
        document=str(row.get("document") or ""),
        series=row.get("series") or None,
        movementDate=_iso_date(str(row.get("movement_date") or "")),
        sequence=row.get("sequence_number") or None,
        tm=row.get("tm") or None,
        cf=row.get("cf") or None,
        reference=build_reference(row),
        movementKind=movement.movement_kind,
        isReturn=bool(row.get("is_return")),
        documentType=row.get("document_type") or None,
        entryQuantity=str6(movement.entry_quantity) or "0.000000",
        entryValue=str6(movement.entry_value) or "0.000000",
        outputQuantity=str6(movement.output_quantity) or "0.000000",
        outputValue=str6(movement.output_value) or "0.000000",
        unitCost=str6(movement.unit_cost),
        costAsOfSource=movement.cost_as_of_source,
        runningQuantity=str6(movement.running_quantity),
        runningValue=str6(movement.running_value),
    )


def _iso_date(raw: str) -> str:
    text = raw.strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def _block_dto(block: dict[str, Any]) -> StockKardexBlock:
    opening_q = block["opening_quantity"]
    opening_v = block["opening_value"]
    closing_q = (
        opening_q + block["entry_quantity"] - block["output_quantity"]
    )
    closing_v = (
        opening_v + block["entry_value"] - block["output_value"]
    )
    has_snapshot = bool(block["has_opening_snapshot"])
    return StockKardexBlock(
        productCode=block["product_code"],
        description=block.get("description"),
        productType=block.get("product_type"),
        unit=block.get("unit"),
        branchCode=block["branch_code"],
        warehouse=block["warehouse"],
        openingQuantity=str6(opening_q) if has_snapshot else "0.000000",
        openingValue=str6(opening_v) if has_snapshot else "0.000000",
        entryQuantityTotal=str6(block["entry_quantity"]) or "0.000000",
        entryValueTotal=str6(block["entry_value"]) or "0.000000",
        outputQuantityTotal=str6(block["output_quantity"]) or "0.000000",
        outputValueTotal=str6(block["output_value"]) or "0.000000",
        closingQuantity=str6(closing_q),
        closingValue=str6(closing_v),
        movementCount=int(block["movement_count"]),
        hasOpeningSnapshot=has_snapshot,
    )


def _totals_dto(universe: KardexUniverse) -> StockKardexTotals | None:
    if universe.status == STATUS_SOURCE_MISSING:
        return None
    totals = universe.totals()
    return StockKardexTotals(
        movementCount=totals["movementCount"],
        blockCount=totals["blockCount"],
        entryQuantity=str6(totals["entryQuantity"]) or "0.000000",
        entryValue=str6(totals["entryValue"]) or "0.000000",
        outputQuantity=str6(totals["outputQuantity"]) or "0.000000",
        outputValue=str6(totals["outputValue"]) or "0.000000",
        netQuantity=str6(totals["netQuantity"]) or "0.000000",
        netValue=str6(totals["netValue"]) or "0.000000",
        openingValue=str6(totals["openingValue"]),
        closingValue=str6(totals["closingValue"]),
    )


def _provenance(request: StockKardexQueryRequest, universe: KardexUniverse) -> dict[str, Any]:
    return {
        "engine": R06_ENGINE_ID,
        "officialProducer": R06_OFFICIAL_PRODUCER,
        "officialProcedure": "matr910_dlp",
        "snapshotDate": request.opening_snapshot_date_iso(),
        "movementWindowStart": request.period_start_iso(),
        "movementWindowEnd": request.reference_date_iso(),
        "documentKind": request.document_kind,
        "asOfConvention": "as_of_ttat_post_close",
        "costAsOfBoundary": request.as_of_boundary_iso(),
        "costAsOfTtatMovements": universe.ttat_applied_count,
        "openingBalanceSource": "sb9_previous_month_end",
        "kardexOutputsNotCpv": True,
    }


class GetStockKardexUseCase:
    """R06 movement list — paginated lines + page product blocks."""

    def __init__(
        self,
        repository: StockKardexRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: StockKardexQueryRequest,
        *,
        user_subject: str | None,
    ) -> StockKardexResponse:
        universe = load_kardex_universe(
            repository=self._repository,
            scope_resolver=self._scope_resolver,
            request=request,
            user_subject=user_subject,
        )

        movements = list(universe.movements)
        if request.movement_kind == MOVEMENT_KIND_ENTRY:
            movements = [
                m for m in movements if m.movement_kind == MOVEMENT_KIND_ENTRY
            ]
        elif request.movement_kind == MOVEMENT_KIND_OUTPUT:
            movements = [
                m for m in movements if m.movement_kind == MOVEMENT_KIND_OUTPUT
            ]

        movements.sort(
            key=lambda m: _sort_key(m, request.sort),
            reverse=request.sort_dir == "desc",
        )

        total_items = len(movements)
        start = (request.page - 1) * request.page_size
        page_rows = movements[start : start + request.page_size]

        page_blocks_keys = {
            (
                str(m.raw.get("branch_code") or ""),
                str(m.raw.get("warehouse") or ""),
                str(m.raw.get("product_code") or ""),
            )
            for m in page_rows
        }
        blocks = [
            universe.blocks[key]
            for key in sorted(
                page_blocks_keys, key=lambda k: (k[2], k[0], k[1])
            )
            if key in universe.blocks
        ]

        parity_status = (
            PARITY_STATUS_PENDING
            if universe.status != STATUS_SOURCE_MISSING
            else PARITY_STATUS_TEST_NOT_RUN
        )
        parity_note = (
            PARITY_NOTE_R07
            if request.document_kind == DOCUMENT_KIND_INVENT
            else PARITY_NOTE_R06
        )

        return StockKardexResponse(
            report=report_name(request.document_kind),
            period=request.period,
            referenceDate=request.reference_date_iso(),
            dataAsOf=(
                request.reference_date_iso()
                if universe.status != STATUS_SOURCE_MISSING
                else None
            ),
            branchCode=request.branch,
            warehouse=request.warehouse,
            documentKind=request.document_kind,
            productCode=request.product_code,
            status=universe.status,
            branchesAvailable=universe.branches_available,
            branchesMissing=universe.branches_missing,
            totals=_totals_dto(universe),
            pagination={
                "page": request.page,
                "page_size": request.page_size,
                "total_items": total_items,
                "total_pages": (
                    (total_items + request.page_size - 1)
                    // request.page_size
                ),
            },
            items=[_movement_dto(m) for m in page_rows],
            blocks=[_block_dto(block) for block in blocks],
            parityStatus=parity_status,
            parityNotes=(
                [parity_note]
                if universe.status != STATUS_SOURCE_MISSING
                else []
            ),
            provenance=_provenance(request, universe),
        )
