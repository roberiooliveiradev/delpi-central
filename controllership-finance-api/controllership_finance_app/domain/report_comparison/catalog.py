"""GATE A — real-capability catalog of the closing reports (HEAD truth).

Every entry is derived from an effectively implemented api-delpi
contract — never from a TARGET. Reports without a governed contract
(R04/R09/R12/R15 pending; R13/R14 external) are intentionally absent:
the engine answers ``unsupported_report`` / ``INSUFFICIENT_EVIDENCE``
instead of pretending comparability.

For each report the catalog records: the governed endpoint, the
allowlisted subject filters, the measures it can expose (unit + kind +
extraction path inside the producer ``data`` envelope), the complete
breakdowns usable for grain diffs, and the document-level keys when a
reliable identity exists.

Breakdown rule: only producer-owned complete aggregations are listed —
top-N lists (``topProductsByCost``, ``topDocuments``) are deliberately
excluded so a truncated ranking is never presented as complete.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MeasureSpec:
    """One measurable quantity of a report.

    ``path`` is a dot path inside the producer ``data`` object for flat
    measures; ``grain_key`` names the breakdown list that supplies the
    per-grain values when ``grain != "total"``.
    """

    unit: str  # "BRL" | "count" | "quantity"
    kind: str  # "currency" | "count" | "quantity"
    path: str | None = None  # dot path inside data (e.g. "totals.outputValue")
    # Settlement groups are a list — sum matching the subject ``side``.
    groups_sum: str | None = None  # field inside groups[] to sum


@dataclass(frozen=True)
class GrainSpec:
    """A complete producer-side breakdown usable for grain diffs."""

    list_path: str  # dot path to the breakdown list
    key_field: str  # field holding the grain key inside each row
    value_fields: dict[str, str]  # measure id -> row field


@dataclass(frozen=True)
class ReportCapability:
    report_id: str
    label: str
    endpoint: str  # upstream api-delpi path
    measures: dict[str, MeasureSpec]
    grains: dict[str, GrainSpec]
    allowed_filters: frozenset[str]  # subject.filters allowlist
    default_measure: str = ""  # measure used when request omits one
    document_key_fields: tuple[str, ...] = ()  # reliable identity fields
    clara_capability: str = ""
    source: str = ""
    parity: str = "PENDING"
    semantics: str = ""
    extra_params: dict[str, str] = field(default_factory=dict)


_TOTAL = "total"

# ------------------------------------------------------------------
# measure paths per report — producer `data` object conventions
# ------------------------------------------------------------------

_KARDEX_MEASURES = {
    "entryValue": MeasureSpec("BRL", "currency", "totals.entryValue"),
    "outputValue": MeasureSpec("BRL", "currency", "totals.outputValue"),
    "netValue": MeasureSpec("BRL", "currency", "totals.netValue"),
    "openingValue": MeasureSpec("BRL", "currency", "totals.openingValue"),
    "closingValue": MeasureSpec("BRL", "currency", "totals.closingValue"),
    "entryQuantity": MeasureSpec(
        "quantity", "quantity", "totals.entryQuantity"
    ),
    "outputQuantity": MeasureSpec(
        "quantity", "quantity", "totals.outputQuantity"
    ),
    "netQuantity": MeasureSpec(
        "quantity", "quantity", "totals.netQuantity"
    ),
    "movementCount": MeasureSpec("count", "count", "totals.movementCount"),
    "blockCount": MeasureSpec("count", "count", "totals.blockCount"),
}

_KARDEX_GRAINS = {
    "product_type": GrainSpec("summariesByType", "productType", {"entryValue":"entryValue","outputValue":"outputValue","netValue":"netValue","entryQuantity":"entryQuantity","outputQuantity":"outputQuantity","netQuantity":"netQuantity","movementCount":"movementCount"}),
    "warehouse": GrainSpec("summariesByWarehouse", "warehouse", {"entryValue":"entryValue","outputValue":"outputValue","netValue":"netValue","entryQuantity":"entryQuantity","outputQuantity":"outputQuantity","netQuantity":"netQuantity","movementCount":"movementCount"}),
}

REPORT_CATALOG: dict[str, ReportCapability] = {
    "R01": ReportCapability(
        report_id="R01",
        default_measure="totalAmount",
        label="Baixas a pagar (SE5)",
        endpoint="/financeiro/settlements/summary",
        measures={
            "totalAmount": MeasureSpec(
                "BRL", "currency", groups_sum="totalAmount"
            ),
            "eventCount": MeasureSpec(
                "count", "count", groups_sum="eventCount"
            ),
        },
        grains={
            "nature": GrainSpec("groups", "natureCode", {"totalAmount":"totalAmount","eventCount":"eventCount"}),
            "movement_type": GrainSpec("groups", "movementType", {"totalAmount":"totalAmount","eventCount":"eventCount"}),
        },
        allowed_filters=frozenset({"side", "nature_code", "movement_type"}),
        clara_capability="read(report.settlements_summary)",
        source="protheus_se5",
        semantics=(
            "Baixas financeiras por competência de caixa (E5_DATA) — "
            "consulta operacional, não o relatório oficial."
        ),
        extra_params={"side": "payable"},
    ),
    "R02": ReportCapability(
        report_id="R02",
        default_measure="totalAmount",
        label="Baixas a receber (SE5)",
        endpoint="/financeiro/settlements/summary",
        measures={
            "totalAmount": MeasureSpec(
                "BRL", "currency", groups_sum="totalAmount"
            ),
            "eventCount": MeasureSpec(
                "count", "count", groups_sum="eventCount"
            ),
        },
        grains={
            "nature": GrainSpec("groups", "natureCode", {"totalAmount":"totalAmount","eventCount":"eventCount"}),
            "movement_type": GrainSpec("groups", "movementType", {"totalAmount":"totalAmount","eventCount":"eventCount"}),
        },
        allowed_filters=frozenset({"side", "nature_code", "movement_type"}),
        clara_capability="read(report.settlements_summary)",
        source="protheus_se5",
        semantics=(
            "Baixas financeiras por competência de caixa (E5_DATA) — "
            "consulta operacional, não o relatório oficial."
        ),
        extra_params={"side": "receivable"},
    ),
    "R03": ReportCapability(
        report_id="R03",
        default_measure="stockTotal",
        label="Posição de estoque (SB9/SB1)",
        endpoint="/financeiro/stock-inventory",
        measures={
            "stockTotal": MeasureSpec("BRL", "currency", "stockTotal"),
            "processPhysicalTotal": MeasureSpec(
                "BRL", "currency", "processPhysicalTotal"
            ),
            "processAllocatedTotal": MeasureSpec(
                "BRL", "currency", "processAllocatedTotal"
            ),
            "processTotal": MeasureSpec(
                "BRL", "currency", "processTotal"
            ),
            "grandTotal": MeasureSpec("BRL", "currency", "grandTotal"),
            "historicalTotal": MeasureSpec(
                "BRL", "currency", "historicalTotal"
            ),
        },
        grains={
            "product_type": GrainSpec("summariesByType", "productType", {"totalStockValue":"totalStockValue","stockTotal":"totalStockValue"}),
            "warehouse": GrainSpec("summariesByWarehouse", "warehouse", {"totalStockValue":"totalStockValue","stockTotal":"totalStockValue"}),
        },
        allowed_filters=frozenset({"report_scope", "warehouse"}),
        clara_capability="read(report.stock_inventory)",
        source="protheus_sb9_sb1",
        semantics=(
            "Snapshot posicional SB9 (estático no corte) — não é o "
            "MATR460/P7 oficial."
        ),
    ),
    "R05": ReportCapability(
        report_id="R05",
        default_measure="closingBalance",
        label="Entradas/Saídas (MATR320)",
        endpoint="/financeiro/stock-movements",
        measures={
            m: MeasureSpec("BRL", "currency", f"totals.{m}")
            for m in (
                "openingBalance",
                "closingBalance",
                "netMovement",
                "purchases",
                "internalMovements",
                "productionRequisitions",
                "transfers",
                "production",
                "sales",
                "salesReturns",
                "purchaseReturns",
                "thirdPartyIn",
                "thirdPartyOut",
            )
        },
        grains={
            "product_type": GrainSpec("rows", "productType", {"sales":"sales","purchases":"purchases","netMovement":"netMovement","closingBalance":"closingBalance","openingBalance":"openingBalance"}),
        },
        allowed_filters=frozenset({"report_scope"}),
        clara_capability="read(report.stock_movements)",
        source="protheus_sd1_sd2_sd3_sb9",
        semantics=(
            "Fluxo valorizado do mês por tipo de produto (equação de "
            "saldo BR-R05-006) — consulta operacional."
        ),
    ),
    "R06": ReportCapability(
        report_id="R06",
        default_measure="outputValue",
        label="Kardex (MATR910)",
        endpoint="/financeiro/stock-kardex/summary",
        measures=dict(_KARDEX_MEASURES),
        grains=dict(_KARDEX_GRAINS),
        allowed_filters=frozenset(
            {"warehouse", "product_code", "product_type"}
        ),
        document_key_fields=("branchCode", "document", "series"),
        clara_capability="read(report.stock_kardex_summary)",
        source="protheus_sd1_sd2_sd3_sb9_ttat",
        semantics=(
            "Kardex valorizado (movimentos SD1/SD2/SD3 + custo as-of "
            "TTAT) — eixo data de movimento, convenção TTAT."
        ),
    ),
    "R07": ReportCapability(
        report_id="R07",
        default_measure="outputValue",
        label="Ajustes de inventário (INVENT)",
        endpoint="/financeiro/inventory-adjustments/summary",
        measures=dict(_KARDEX_MEASURES),
        grains=dict(_KARDEX_GRAINS),
        allowed_filters=frozenset({"warehouse", "product_code"}),
        clara_capability="read(report.inventory_adjustments_summary)",
        source="protheus_sd3_invent_ttat",
        semantics=(
            "Recorte INVENT (D3_DOC='INVENT', TES 499/DE0 + 999/RE0) "
            "do mesmo motor MATR910 — subconjunto dos movimentos R06."
        ),
    ),
    "R08": ReportCapability(
        report_id="R08",
        default_measure="grandTotal",
        label="Material em processo (MATR989/H02)",
        endpoint="/financeiro/work-in-process",
        measures={
            "physicalTotal": MeasureSpec(
                "BRL", "currency", "physicalTotal"
            ),
            "allocatedTotal": MeasureSpec(
                "BRL", "currency", "allocatedTotal"
            ),
            "grandTotal": MeasureSpec("BRL", "currency", "grandTotal"),
        },
        grains={
            "product_type": GrainSpec("summariesByType", "productType", {"grandTotal":"totalValue","physicalTotal":"physicalTotal","allocatedTotal":"allocatedTotal"}),
        },
        allowed_filters=frozenset({"report_scope", "warehouse"}),
        clara_capability="read(report.work_in_process)",
        source="protheus_sb9_sd3_sc2_loc99",
        semantics=(
            "Material em processo — físico loc99 (sem-OP) + alocado a "
            "OPs (SD3/SC2); universo disjunto do estoque P7."
        ),
    ),
    "R10": ReportCapability(
        report_id="R10",
        default_measure="totalValue",
        label="Despesas por centro de custo",
        endpoint="/financeiro/cost-center-expenses",
        measures={
            "totalValue": MeasureSpec(
                "BRL", "currency", "summary.totalValue"
            ),
            "lineCount": MeasureSpec(
                "count", "count", "summary.lineCount"
            ),
            "documentCount": MeasureSpec(
                "count", "count", "summary.documentCount"
            ),
            "costCenterCount": MeasureSpec(
                "count", "count", "summary.costCenterCount"
            ),
            "supplierCount": MeasureSpec(
                "count", "count", "summary.supplierCount"
            ),
            "findingCount": MeasureSpec(
                "count", "count", "summary.findingCount"
            ),
            "unclassifiedCount": MeasureSpec(
                "count", "count", "summary.unclassifiedCount"
            ),
        },
        grains={
            "cost_center": GrainSpec("summary.byCostCenter", "costCenter", {"totalValue":"totalValue","lineCount":"lineCount","findingCount":"findingCount"}),
            "product_type": GrainSpec("summary.byProductType", "productType", {"totalValue":"totalValue","lineCount":"lineCount"}),
        },
        allowed_filters=frozenset(
            {
                "universe",
                "view",
                "cost_center",
                "product_code",
                "document",
                "supplier_code",
                "tes",
            }
        ),
        document_key_fields=("branchCode", "document", "series"),
        clara_capability="read(report.cost_center_expenses)",
        source="protheus_sd1_sb1_sa2_ctt",
        semantics=(
            "Seleção histórica EDAPP (eixo D1_DTDIGIT) — universos "
            "calculation × investigation são partições estritas, "
            "totais nunca somados."
        ),
        extra_params={"universe": "calculation"},
    ),
    "R11": ReportCapability(
        report_id="R11",
        default_measure="totalValue",
        label="NF a desconsiderar",
        endpoint="/financeiro/billing-exclusion-roster",
        measures={
            "totalValue": MeasureSpec(
                "BRL", "currency", "summary.totalValue"
            ),
            "lineCount": MeasureSpec(
                "count", "count", "summary.lineCount"
            ),
            "documentCount": MeasureSpec(
                "count", "count", "summary.documentCount"
            ),
            "customerCount": MeasureSpec(
                "count", "count", "summary.customerCount"
            ),
            "zeroCostCount": MeasureSpec(
                "count", "count", "summary.zeroCostCount"
            ),
            "missingStockSiblingDocumentCount": MeasureSpec(
                "count", "count", "summary.missingStockSiblingDocumentCount"
            ),
            "findingCount": MeasureSpec(
                "count", "count", "summary.findingCount"
            ),
            "candidateLineCount": MeasureSpec(
                "count", "count", "summary.candidateLineCount"
            ),
            "outOfCriteriaLineCount": MeasureSpec(
                "count", "count", "summary.outOfCriteriaLineCount"
            ),
        },
        grains={
            "tes": GrainSpec("summary.byTes", "tes", {"totalValue":"totalValue","lineCount":"lineCount"}),
            "product_group": GrainSpec("summary.byProductGroup", "productGroup", {"totalValue":"totalValue","lineCount":"lineCount"}),
        },
        allowed_filters=frozenset(
            {
                "view",
                "product_group",
                "product_code",
                "document",
                "customer_code",
                "tes",
            }
        ),
        document_key_fields=("branchCode", "document", "series"),
        clara_capability="read(report.billing_exclusion_roster)",
        source="protheus_sd2_sf4_sb1_sa1",
        semantics=(
            "Roster investigativo (eixo D2_EMISSAO; predicado histórico "
            "observado 9035∩594 — E11a/E11b TO_INVENTORY) — nenhuma "
            "nota é excluída automaticamente."
        ),
        extra_params={"view": "candidates"},
    ),
    "CPV": ReportCapability(
        report_id="CPV",
        default_measure="cpvTotal",
        label="CPV gerencial (SD2/CFOP)",
        endpoint="/financeiro/cpv",
        measures={
            "cpvTotal": MeasureSpec("BRL", "currency", "summary.cpvTotal"),
            "totalMovements": MeasureSpec(
                "count", "count", "summary.totalMovements"
            ),
            "totalQuantity": MeasureSpec(
                "quantity", "quantity", "summary.totalQuantity"
            ),
        },
        grains={
            "cfop": GrainSpec("byCfop", "cfop", {"cpvTotal":"cpvTotal","totalMovements":"movementCount","totalQuantity":"totalQuantity"}),
            "tm": GrainSpec("byTm", "tm", {"cpvTotal":"cpvTotal","totalMovements":"movementCount","totalQuantity":"totalQuantity"}),
        },
        allowed_filters=frozenset({"top_limit"}),
        clara_capability="read(report.cpv)",
        source="protheus_sd2_custos",
        semantics=(
            "CPV gerencial — SUM(D2_CUSTO1) por CFOP de venda com "
            "custo corrente (asOfConvention 'live'); não é o total de "
            "saídas do kardex."
        ),
    ),
}

# Reports without an implemented contract — the honest negative set.
UNIMPLEMENTED_REPORTS: dict[str, str] = {
    "R04": "PENDING_CONTRACT — fonte/owner não confirmados.",
    "R09": "PENDING_CONTRACT — DLP204 sem SP implementada (E9).",
    "R12": "STATE_VIEW — projeção de estado implementada; comparação monetária não se aplica.",
    "R13": "EXTERNAL — evidência documental externa, sem contrato numérico.",
    "R14": "EXTERNAL — evidência documental externa, sem contrato numérico.",
    "R15": "STATE_VIEW — projeção de estado implementada; comparação monetária não se aplica.",
}
