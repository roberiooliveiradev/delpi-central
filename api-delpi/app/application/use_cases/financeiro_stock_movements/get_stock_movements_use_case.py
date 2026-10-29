"""Read the R05 "Entradas e Saídas" summary (MATR320 rule, doc 85 §5).

Composition per product type: SD1/SD2 movement columns via the SF4 TES
join, SD3 movement columns via the CF/OP classification, closing
balance (SA) from the same SB9 snapshot universe the P7 engine reads.
Opening balance is the derived column ``SA − net movement``
(BR-R05-006) — never a stored register.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    STATUS_AVAILABLE,
    STATUS_INCOMPLETE,
    STATUS_NO_MATCHING_ITEMS,
    STATUS_SOURCE_MISSING,
)
from app.application.dto.financeiro_stock_movements.stock_movements_request import (
    StockMovementsQueryRequest,
)
from app.application.dto.financeiro_stock_movements.stock_movements_response import (
    StockMovementsResponse,
    StockMovementsTypeRow,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.financeiro_stock_movements.stock_movements_repository_port import (
    StockMovementsRepositoryPort,
)

REPORT_STOCK_MOVEMENTS = "stock-movements"
R05_ENGINE_ID = "minha-delpi-r05-movements-engine"
R05_OFFICIAL_PRODUCER = "matr320"

PARITY_NOTE_R05 = (
    "Motor R05 com a classificação MATR320 comprovada célula a célula "
    "(130/130) para a competência 09/2026 filial 01; leitura no estado "
    "corrente das tabelas — retificações retroativas posteriores à "
    "emissão oficial podem produzir drift legítimo (BR-R05-008); "
    "paridade por competência pendente de homologação."
)

_ZERO = Decimal("0")


def _dec(value) -> Decimal:
    if value is None or value == "":
        return _ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _ZERO


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


class GetStockMovementsUseCase:
    def __init__(
        self,
        repository: StockMovementsRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: StockMovementsQueryRequest,
        *,
        user_subject: str | None,
    ) -> StockMovementsResponse:
        # Same fail-closed dataset gate as the sibling P7 route — the
        # reports share one authorized Protheus dataset (doc 49 §8).
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

        base = {
            "report": REPORT_STOCK_MOVEMENTS,
            "period": request.period,
            "referenceDate": request.reference_date_iso(),
            "branchCode": request.branch,
            "reportScope": request.report_scope,
            "branchesAvailable": available,
            "branchesMissing": missing,
        }

        sd1 = {
            row.get("product_type"): row
            for row in self._repository.sd1_by_type(
                branches=branches,
                period_start=request.period_start(),
                period_end=snapshot_date,
                product_types=product_types,
            )
        }
        sd2 = {
            row.get("product_type"): row
            for row in self._repository.sd2_by_type(
                branches=branches,
                period_start=request.period_start(),
                period_end=snapshot_date,
                product_types=product_types,
            )
        }
        sd3 = {
            row.get("product_type"): row
            for row in self._repository.sd3_by_type(
                branches=branches,
                period_start=request.period_start(),
                period_end=snapshot_date,
                product_types=product_types,
            )
        }
        sa_by_type: dict[str | None, Decimal] = {}
        if available:
            for row in self._repository.closing_balance_by_type(
                snapshot_date=snapshot_date,
                branches=branches,
                product_types=product_types,
            ):
                sa_by_type[row.get("product_type")] = _dec(
                    row.get("total_stock_value")
                )

        type_keys = set(sd1) | set(sd2) | set(sd3) | set(sa_by_type)

        rows: list[StockMovementsTypeRow] = []
        totals = {key: _ZERO for key in _MOVEMENT_KEYS} | {
            "openingBalance": _ZERO,
            "closingBalance": _ZERO,
            "netMovement": _ZERO,
        }
        for product_type in sorted(type_keys, key=lambda t: (t is None, t)):
            m1, m2, m3 = (
                sd1.get(product_type) or {},
                sd2.get(product_type) or {},
                sd3.get(product_type) or {},
            )
            cols = {
                "purchases": _dec(m1.get("purchases")),
                "internalMovements": _dec(m3.get("internal_movements")),
                "productionRequisitions": _dec(
                    m3.get("production_requisitions")
                ),
                "transfers": _dec(m3.get("transfers")),
                "production": _dec(m3.get("production")),
                "sales": _dec(m2.get("sales")),
                "processTransfersMemo": _dec(m3.get("process_transfers")),
                "salesReturns": _dec(m1.get("sales_returns")),
                "purchaseReturns": _dec(m2.get("purchase_returns")),
                "thirdPartyIn": _dec(m1.get("third_party_in")),
                "thirdPartyOut": _dec(m2.get("third_party_out")),
            }
            # Balance equation (BR-R05-006): SA = SI + Compras + MovInt +
            # Requis + Transf + Produção − Vendas + DevV − DevC + EntPT −
            # SaiPT. process_transfers stays OUT — it is the memo column.
            closing = sa_by_type.get(product_type)
            if available and product_type not in sa_by_type:
                # SB9 exists but no balance row for the type — real zero
                # stock at month end, not an unknown measure.
                closing = _ZERO
            net = (
                cols["purchases"]
                + cols["internalMovements"]
                + cols["productionRequisitions"]
                + cols["transfers"]
                + cols["production"]
                - cols["sales"]
                + cols["salesReturns"]
                - cols["purchaseReturns"]
                + cols["thirdPartyIn"]
                - cols["thirdPartyOut"]
            )
            opening = None if closing is None else closing - net
            rows.append(
                StockMovementsTypeRow(
                    productType=product_type,
                    openingBalance=_str6(opening),
                    **{key: _str6(value) for key, value in cols.items()},
                    closingBalance=_str6(closing),
                    netMovement=_str6(net),
                )
            )
            for key, value in cols.items():
                totals[key] += value
            if opening is not None:
                totals["openingBalance"] += opening
            if closing is not None:
                totals["closingBalance"] += closing
            totals["netMovement"] += net

        if not available:
            status = STATUS_SOURCE_MISSING
        elif missing:
            status = STATUS_INCOMPLETE
        elif not rows:
            status = STATUS_NO_MATCHING_ITEMS
        else:
            status = STATUS_AVAILABLE

        totals_out = {
            key: _str6(value) for key, value in totals.items()
        }
        if not available:
            # No snapshot anywhere — no balance can be certified (never
            # a fabricated zero total).
            totals_out["openingBalance"] = None
            totals_out["closingBalance"] = None
            totals_out["netMovement"] = None

        return StockMovementsResponse(
            **base,
            dataAsOf=request.reference_date_iso() if available else None,
            status=status,
            rows=rows,
            totals=totals_out,
            parityStatus=PARITY_STATUS_PENDING if available
            else "TEST_NOT_RUN",
            parityNotes=[PARITY_NOTE_R05] if available else [],
            provenance={
                "engine": R05_ENGINE_ID,
                "officialProducer": R05_OFFICIAL_PRODUCER,
                "officialProcedure": "mat056",
                "snapshotDate": request.reference_date_iso(),
                "movementWindowStart": request.period_start_iso(),
                "movementWindowEnd": request.reference_date_iso(),
                "reportScope": request.report_scope,
                "asOfConvention": "query_time",
            },
        )


_MOVEMENT_KEYS = (
    "purchases",
    "internalMovements",
    "productionRequisitions",
    "transfers",
    "production",
    "sales",
    "processTransfersMemo",
    "salesReturns",
    "purchaseReturns",
    "thirdPartyIn",
    "thirdPartyOut",
)
