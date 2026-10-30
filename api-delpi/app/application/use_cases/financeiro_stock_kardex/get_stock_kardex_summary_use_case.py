"""Read the R06 stock-kardex global summary (MATR910, doc 122 §4).

Global aggregates over the full authorized universe: totals, breakdown
by product type and by warehouse, and the top-product ranking by output
cost — never computed from a page slice.
"""

from __future__ import annotations

from decimal import Decimal

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    PARITY_STATUS_TEST_NOT_RUN,
    STATUS_SOURCE_MISSING,
)
from app.application.dto.financeiro_stock_kardex.constantes import (
    DOCUMENT_KIND_INVENT,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.dto.financeiro_stock_kardex.stock_kardex_response import (
    StockKardexSummaryResponse,
    StockKardexTopProduct,
    StockKardexTypeSummary,
    StockKardexWarehouseSummary,
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
    load_kardex_universe,
    report_name,
    str6,
)
from .get_stock_kardex_use_case import _provenance, _totals_dto

_TOP_PRODUCTS_LIMIT = 10


class GetStockKardexSummaryUseCase:
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
    ) -> StockKardexSummaryResponse:
        universe = load_kardex_universe(
            repository=self._repository,
            scope_resolver=self._scope_resolver,
            request=request,
            user_subject=user_subject,
        )

        by_type: dict[str | None, dict] = {}
        by_warehouse: dict[tuple[str, str], dict] = {}
        by_product: dict[str, dict] = {}
        for movement in universe.movements:
            row = movement.raw
            ptype = row.get("product_type")
            acc = by_type.setdefault(
                ptype, _new_acc()
            )
            _accumulate(acc, movement)

            wh_key = (
                str(row.get("branch_code") or ""),
                str(row.get("warehouse") or ""),
            )
            _accumulate(by_warehouse.setdefault(wh_key, _new_acc()), movement)

            pcode = str(row.get("product_code") or "")
            prod = by_product.setdefault(
                pcode,
                {**_new_acc(), "description": row.get("description")},
            )
            _accumulate(prod, movement)

        top_products = sorted(
            by_product.items(),
            key=lambda item: (item[1]["output_v"], item[0]),
            reverse=True,
        )[:_TOP_PRODUCTS_LIMIT]

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

        return StockKardexSummaryResponse(
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
            status=universe.status,
            branchesAvailable=universe.branches_available,
            branchesMissing=universe.branches_missing,
            totals=_totals_dto(universe),
            summariesByType=[
                StockKardexTypeSummary(
                    productType=ptype,
                    movementCount=acc["count"],
                    entryQuantity=str6(acc["entry_q"]) or "0.000000",
                    entryValue=str6(acc["entry_v"]) or "0.000000",
                    outputQuantity=str6(acc["output_q"]) or "0.000000",
                    outputValue=str6(acc["output_v"]) or "0.000000",
                )
                for ptype, acc in sorted(
                    by_type.items(), key=lambda i: (i[0] is None, i[0])
                )
            ],
            summariesByWarehouse=[
                StockKardexWarehouseSummary(
                    branchCode=key[0],
                    warehouse=key[1],
                    movementCount=acc["count"],
                    entryQuantity=str6(acc["entry_q"]) or "0.000000",
                    entryValue=str6(acc["entry_v"]) or "0.000000",
                    outputQuantity=str6(acc["output_q"]) or "0.000000",
                    outputValue=str6(acc["output_v"]) or "0.000000",
                )
                for key, acc in sorted(by_warehouse.items())
            ],
            topProductsByCost=[
                StockKardexTopProduct(
                    productCode=pcode,
                    description=prod["description"],
                    movementCount=prod["count"],
                    outputQuantity=str6(prod["output_q"]) or "0.000000",
                    outputValue=str6(prod["output_v"]) or "0.000000",
                )
                for pcode, prod in top_products
            ],
            parityStatus=parity_status,
            parityNotes=(
                [parity_note]
                if universe.status != STATUS_SOURCE_MISSING
                else []
            ),
            provenance=_provenance(request, universe),
        )


def _new_acc() -> dict:
    return {
        "count": 0,
        "entry_q": Decimal("0"),
        "entry_v": Decimal("0"),
        "output_q": Decimal("0"),
        "output_v": Decimal("0"),
    }


def _accumulate(acc: dict, movement) -> None:
    acc["count"] += 1
    acc["entry_q"] += movement.entry_quantity
    acc["entry_v"] += movement.entry_value
    acc["output_q"] += movement.output_quantity
    acc["output_v"] += movement.output_value
