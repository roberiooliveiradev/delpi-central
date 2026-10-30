"""Read the dedicated R06 CPV contract (doc 122 §6, D-O1).

Reuses the CANONICAL CPV semantics — ``CpvQueryRepository`` over SD2
with the fixed CFOP set (5101/5124/6101/6124), ``D2_EMISSAO`` window
and ``SUM(D2_CUSTO1)`` — inside the governed financeiro envelope:
dataset scope gate, decimal-preserving totals, provenance and parity
state. The CPV measure is LIVE (PO decision BR-R06-010): it reads the
current ``D2_CUSTO1`` — later official recalculations legitimately
change the measure for the same month, and that is the approved
convention (``asOfConvention: "live"``). It is NOT the kardex output
column and must not be reconciled to it.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    STATUS_AVAILABLE,
)
from app.application.dto.financeiro_stock_kardex.financeiro_cpv_request import (
    FinanceiroCpvRequest,
)
from app.application.dto.supplies.get_cpv_request import GetCPVRequest
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    require_stock_inventory_scope,
)
from app.domain.ports.supplies.cpv_query_repository_port import (
    CpvQueryRepositoryPort,
)

REPORT_FINANCEIRO_CPV = "cpv"
CPV_ENGINE_ID = "minha-delpi-cpv-engine"
CPV_OFFICIAL_PRODUCER = "matr910"
CPV_CFOPS = ("5101", "5124", "6101", "6124")

PARITY_NOTE_CPV = (
    "CPV gerencial com a semântica canônica (SD2, CFOPs 5101/5124/6101/"
    "6124, D2_EMISSAO, D2_CUSTO1 corrente — decisão PO BR-R06-010): "
    "medida viva sujeita a retificações oficiais posteriores; não é o "
    "totalizador de saídas do Kardex e não deve ser reconciliado a ele."
)

_ZERO = Decimal("0")
_Q6 = Decimal("0.000001")


def _dec(value) -> Decimal:
    if value is None or value == "":
        return _ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _ZERO


def _str6(value: Decimal) -> str:
    return str(value.quantize(_Q6))


def _cpv_request(request: FinanceiroCpvRequest) -> GetCPVRequest:
    branch = request.branch
    return GetCPVRequest(
        branch=None if branch == "all" else branch,
        start_date=request.period_start(),
        end_date=request.period_end(),
        top_limit=request.top_limit,
        cfops=CPV_CFOPS,
    )


class GetFinanceiroCpvUseCase:
    def __init__(
        self,
        cpv_repository: CpvQueryRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._cpv_repository = cpv_repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: FinanceiroCpvRequest,
        *,
        user_subject: str | None,
    ) -> dict:
        require_stock_inventory_scope(
            self._scope_resolver, user_subject=user_subject
        )
        cpv_req = _cpv_request(request)

        summary = self._cpv_repository.get_cpv_summary(cpv_req)
        by_cfop = self._cpv_repository.get_cpv_by_cfop(cpv_req)
        by_tm = self._cpv_repository.get_cpv_by_tm(cpv_req)
        top_products = self._cpv_repository.get_cpv_top_products(cpv_req)
        top_documents = self._cpv_repository.get_cpv_top_documents(cpv_req)

        cpv_total = _dec(summary.get("cpv_total"))
        total_movements = int(summary.get("total_movements") or 0)
        total_quantity = _dec(summary.get("total_quantity"))

        return {
            "report": REPORT_FINANCEIRO_CPV,
            "period": request.period,
            "referenceDate": request.period_end(),
            "dataAsOf": request.period_end(),
            "branchCode": request.branch,
            "source": "protheus_sd2_custos",
            "officialR06": False,
            "asOfConvention": "live",
            "cfops": list(CPV_CFOPS),
            "status": STATUS_AVAILABLE,
            "summary": {
                "cpvTotal": _str6(cpv_total),
                "totalMovements": total_movements,
                "totalQuantity": _str6(total_quantity),
                "averageCostPerMovement": _str6(
                    cpv_total / total_movements if total_movements else _ZERO
                ),
                "averageCostPerUnit": _str6(
                    cpv_total / total_quantity
                    if total_quantity != _ZERO
                    else _ZERO
                ),
                "firstMovementDate": str(summary.get("start_date") or ""),
                "lastMovementDate": str(summary.get("end_date") or ""),
            },
            "byCfop": [
                {
                    "cfop": row.get("cfop"),
                    "totalMovements": int(row.get("total_movements") or 0),
                    "totalQuantity": _str6(_dec(row.get("total_quantity"))),
                    "cpvTotal": _str6(_dec(row.get("cpv_total"))),
                }
                for row in by_cfop
            ],
            "byTm": [
                {
                    "tm": row.get("tm"),
                    "cfop": row.get("cfop"),
                    "tesDescription": row.get("tes_description"),
                    "totalMovements": int(row.get("total_movements") or 0),
                    "totalQuantity": _str6(_dec(row.get("total_quantity"))),
                    "cpvTotal": _str6(_dec(row.get("cpv_total"))),
                }
                for row in by_tm
            ],
            "topProducts": [
                {
                    "productCode": (row.get("product_code") or "").strip(),
                    "description": row.get("product_description"),
                    "totalMovements": int(row.get("total_movements") or 0),
                    "totalQuantity": _str6(_dec(row.get("total_quantity"))),
                    "cpvTotal": _str6(_dec(row.get("cpv_total"))),
                }
                for row in top_products
            ],
            "topDocuments": [
                {
                    "document": row.get("document"),
                    "totalMovements": int(row.get("total_movements") or 0),
                    "totalQuantity": _str6(_dec(row.get("total_quantity"))),
                    "cpvTotal": _str6(_dec(row.get("cpv_total"))),
                }
                for row in top_documents
            ],
            "parityStatus": PARITY_STATUS_PENDING,
            "parityNotes": [PARITY_NOTE_CPV],
            "provenance": {
                "engine": CPV_ENGINE_ID,
                "officialProducer": CPV_OFFICIAL_PRODUCER,
                "costField": "D2_CUSTO1",
                "dateField": "D2_EMISSAO",
                "cfopSet": list(CPV_CFOPS),
                "asOfConvention": "live",
                "movementWindowStart": request.period_start(),
                "movementWindowEnd": request.period_end(),
            },
        }
