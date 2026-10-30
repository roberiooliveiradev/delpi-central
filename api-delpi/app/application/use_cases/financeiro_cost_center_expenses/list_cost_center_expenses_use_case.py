"""R10 cost-center-expenses query (doc 126 §§5/16/17, stage-01).

Single engine, two strict universes:

- ``calculation`` — the documented historical selection (axis
  ``D1_DTDIGIT``, thirteen excluded TES, no MP, no benefit lines);
  reproduced 1:1 for 2026-09/01 (353 lines / R$ 169.704,12 / 139 docs /
  46 cost centers — parity baseline recorded in ``selection``).
- ``investigation`` — in-competence SD1 rows the selection excluded
  (MP, excluded TES, benefit lines). Totals are never combined with the
  calculation universe (doc 127 §3 invariant).

Classification, exclusion reasons, findings and aggregates are computed
here over the full authorized row set — one engine for list, export and
the CLARA surface.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.financeiro_cost_center_expenses.constantes import (
    BENEFIT_PRODUCT_GROUP,
    BENEFIT_PRODUCT_TYPE,
    BENEFIT_TES,
    COST_CLASS_UNCLASSIFIED,
    EXCLUDED_TES,
    EXCLUSION_BENEFIT,
    EXCLUSION_RAW_MATERIAL,
    EXCLUSION_TES,
    FINDINGS_CAP,
    RAW_MATERIAL_PRODUCT_TYPE,
    REPORT_ID,
    RULE_COST_CENTER_NOT_IN_CATALOG,
    RULE_DIVERGENT_COST_CLASS,
    RULE_MISSING_COST_CENTER,
    RULE_MP_WITH_COST_CENTER,
    RULE_PRODUCT_COST_CENTER_MISMATCH,
    RULE_UNCLASSIFIED_COST_CLASS,
    SORT_FIELD_COST_CENTER,
    SORT_FIELD_DATE,
    SORT_FIELD_DOCUMENT,
    SORT_FIELD_PRODUCT,
    SORT_FIELD_TOTAL_VALUE,
    UNIVERSE_CALCULATION,
    UNIVERSE_INVESTIGATION,
    VIEW_DIVERGENCES,
    VIEW_UNCLASSIFIED,
)
from app.application.dto.financeiro_cost_center_expenses.cost_center_expenses_request import (
    CostCenterExpensesRequest,
)
from app.application.dto.financeiro_cost_center_expenses.cost_center_expenses_response import (
    CostCenterExpenseFinding,
    CostCenterExpenseItem,
    CostCenterExpensesResponse,
    CostCenterExpenseSummary,
)
from app.application.dto.financeiro_stock_inventory.constantes import (
    PARITY_STATUS_PENDING,
    STATUS_AVAILABLE,
    STATUS_NO_MATCHING_ITEMS,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
    StockInventoryScopeUnavailableError,
)
from app.domain.ports.financeiro_cost_center_expenses.cost_center_expenses_repository_port import (
    CostCenterExpensesRepositoryPort,
)

from ._findings import cost_center_catalog_status, evaluate_findings

Q2 = Decimal("0.01")
Q6 = Decimal("0.000001")

_ENGINE_ID = "r10-cost-center-expenses-v1"
_OFFICIAL_PRODUCER = "EDAPP"

# Parity baseline reproduced live on 2026-09 / branch 01 (evidence:
# 353 SD1 item lines, R$ 169.704,12, 139 documents, 46 cost centers —
# identical to CC matriz.xlsb / SCAGQGA0.XML, doc 126 §2).
_PARITY_BASELINE = {
    "period": "2026-09",
    "branch": "01",
    "lineCount": 353,
    "totalValue": "169704.12",
    "documentCount": 139,
    "costCenterCount": 46,
    "artifact": "CC matriz.xlsb / SCAGQGA0.XML",
    "status": "PROVEN",
}

_RULES_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "ruleId": RULE_MP_WITH_COST_CENTER,
        "description": "Matéria-prima com centro de custo atribuído.",
        "implemented": True,
        "universe": "investigation",
        "evidenceRefs": ["doc-126#DV-R10-01", "doc-85#BR-R10-004"],
    },
    {
        "ruleId": RULE_COST_CENTER_NOT_IN_CATALOG,
        "description": (
            "Centro de custo ausente do cadastro CTT vigente, "
            "sintético ou bloqueado."
        ),
        "implemented": True,
        "universe": "both",
        "limitation": (
            "Validade avaliada no cadastro atual — não comprova a "
            "situação histórica do código na competência."
        ),
        "evidenceRefs": ["doc-126#DV-R10-02", "doc-56#50:35"],
    },
    {
        "ruleId": RULE_PRODUCT_COST_CENTER_MISMATCH,
        "description": "Produto incompatível com o centro de custo.",
        "implemented": False,
        "pendingReason": (
            "E10a — catálogo CC→classe homologado inexistente; "
            "incompatibilidade não é inferida por prefixo."
        ),
        "evidenceRefs": ["doc-126#DV-R10-03", "doc-56#50:10"],
    },
    {
        "ruleId": RULE_MISSING_COST_CENTER,
        "description": "Lançamento de despesa sem centro de custo.",
        "implemented": True,
        "universe": "both",
        "evidenceRefs": ["doc-126#DV-R10-04"],
    },
    {
        "ruleId": RULE_UNCLASSIFIED_COST_CLASS,
        "description": (
            "Despesa sem classificação Direto/Indireto/Adm comprovada."
        ),
        "implemented": True,
        "kind": "status",
        "note": (
            "Classificação não é campo do Protheus (D-01) — toda "
            "linha permanece UNCLASSIFIED até o catálogo E10a."
        ),
        "evidenceRefs": ["doc-126#DV-R10-05", "doc-126#D-01"],
    },
    {
        "ruleId": RULE_DIVERGENT_COST_CLASS,
        "description": "Classificação divergente da esperada.",
        "implemented": False,
        "pendingReason": (
            "E10a/E10b — sem catálogo esperado homologado nem "
            "persistência de revisão."
        ),
        "evidenceRefs": ["doc-126#DV-R10-06"],
    },
)

_PARITY_NOTES = [
    "Consulta operacional — não é a emissão oficial do relatório R10; "
    "paridade oficial permanece PENDING de homologação humana (G6).",
    "Seleção histórica reproduzida para 2026-09/filial 01: 353 linhas, "
    "R$ 169.704,12, 139 documentos, 46 centros de custo — idêntica ao "
    "artefato documentado.",
    "Achados são POSSIBLE_DIVERGENCE — nunca erro confirmado; correção "
    "é atividade humana externa no TOTVS/Protheus.",
]


class ListCostCenterExpensesUseCase:
    """Lists the R10 expense lines of one universe with findings."""

    def __init__(
        self,
        *,
        repository: CostCenterExpensesRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: CostCenterExpensesRequest,
        *,
        user_subject: str | None,
    ) -> CostCenterExpensesResponse:
        scope = self._scope_resolver.resolve(user_subject=user_subject)
        if not scope.resolved:
            raise StockInventoryScopeUnavailableError(scope.reason)

        rows = self._repository.fetch_lines(
            period_start=request.period_start(),
            period_end=request.period_end(),
            branches=request.requested_branches(),
            cost_center=request.cost_center,
            product_code=request.product_code,
            document=request.document,
            supplier_code=request.supplier_code,
            tes=request.tes,
        )

        # Universe split — the official predicate is evaluated once per
        # row; the two universes are strict partitions of the fetched set.
        enriched: list[dict[str, Any]] = []
        for row in rows:
            exclusion = _calculation_exclusion(row)
            inside = exclusion is None
            if request.universe == UNIVERSE_CALCULATION and not inside:
                continue
            if request.universe == UNIVERSE_INVESTIGATION and inside:
                continue
            row = dict(row)
            row["calculation_exclusion"] = exclusion
            row["cc_catalog_status"] = cost_center_catalog_status(row)
            row["findings"] = evaluate_findings(
                row, universe=request.universe
            )
            enriched.append(row)

        summary = _build_summary(enriched)

        findings: list[dict[str, Any]] = []
        if request.include_findings:
            for row in enriched:
                findings.extend(row["findings"])
        findings_truncated = len(findings) > FINDINGS_CAP
        if findings_truncated:
            findings = findings[:FINDINGS_CAP]

        # View narrows presentation only — the summary always covers the
        # full authorized universe after universe+user filters.
        view_rows = _apply_view(enriched, view=request.view)
        view_rows = _sort_rows(
            view_rows, sort=request.sort, sort_dir=request.sort_dir
        )

        total_items = len(view_rows)
        offset = (request.page - 1) * request.page_size
        page_rows = view_rows[offset : offset + request.page_size]

        return CostCenterExpensesResponse(
            report=REPORT_ID,
            period=request.period,
            branchCode=request.branch,
            universe=request.universe,
            view=request.view,
            status=(
                STATUS_AVAILABLE if total_items else STATUS_NO_MATCHING_ITEMS
            ),
            selection=_selection_block(request),
            pagination={
                "page": request.page,
                "page_size": request.page_size,
                "total_items": total_items,
                "universe_items": len(enriched),
            },
            summary=summary,
            findings=[
                CostCenterExpenseFinding(
                    findingId=f"{f['ruleId']}-{f['lineId']}",
                    ruleId=f["ruleId"],
                    status=f["status"],
                    lineId=f["lineId"],
                    sourceRecord=f["sourceRecord"],
                    observedValues=f["observedValues"],
                    findingExplanation=f["findingExplanation"],
                    evidenceRefs=f["evidenceRefs"],
                    erpReviewGuidance=f["erpReviewGuidance"],
                )
                for f in findings
            ],
            findingsTruncated=findings_truncated,
            rulesCatalog=list(_RULES_CATALOG),
            parityStatus=PARITY_STATUS_PENDING,
            parityNotes=list(_PARITY_NOTES),
            provenance={
                "engine": _ENGINE_ID,
                "officialProducer": _OFFICIAL_PRODUCER,
                "sourceTables": "SD1010+SB1010+SA2010+CTT010",
                "artifact": "CC matriz.xlsb / SCAGQGA0.XML",
                "periodStart": request.period_start(),
                "periodEnd": request.period_end(),
                "cttCatalogSnapshot": "current",
            },
            items=[_to_item(r, universe=request.universe) for r in page_rows],
        )


def _is_benefit_line(row: dict[str, Any]) -> bool:
    return (
        (row.get("tes") or "").strip() == BENEFIT_TES
        and (row.get("product_type") or "").strip()
        == BENEFIT_PRODUCT_TYPE
        and not (row.get("cost_center") or "").strip()
        and (row.get("product_group") or "").strip()
        == BENEFIT_PRODUCT_GROUP
    )


def _calculation_exclusion(row: dict[str, Any]) -> str | None:
    """Why the row is outside the official selection — or ``None``."""
    tes = (row.get("tes") or "").strip()
    product_type = (row.get("product_type") or "").strip()
    if _is_benefit_line(row):
        return EXCLUSION_BENEFIT
    if tes in EXCLUDED_TES:
        return EXCLUSION_TES
    if product_type == RAW_MATERIAL_PRODUCT_TYPE:
        return EXCLUSION_RAW_MATERIAL
    return None


def _apply_view(
    rows: list[dict[str, Any]], *, view: str
) -> list[dict[str, Any]]:
    if view == VIEW_DIVERGENCES:
        return [r for r in rows if r["findings"]]
    if view == VIEW_UNCLASSIFIED:
        return [
            r for r in rows if r.get("cost_class", COST_CLASS_UNCLASSIFIED)
            == COST_CLASS_UNCLASSIFIED
        ]
    return rows


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _sort_rows(
    rows: list[dict[str, Any]], *, sort: str, sort_dir: str
) -> list[dict[str, Any]]:
    def base(row: dict[str, Any]):
        return (
            str(row.get("document") or ""),
            str(row.get("sequence_number") or ""),
            str(row.get("item") or ""),
            int(row.get("line_id") or 0),
        )

    if sort == SORT_FIELD_DATE:
        key = lambda r: (str(r.get("entry_date") or ""), *base(r))
    elif sort == SORT_FIELD_DOCUMENT:
        key = lambda r: base(r)
    elif sort == SORT_FIELD_COST_CENTER:
        key = lambda r: (str(r.get("cost_center") or ""), *base(r))
    elif sort == SORT_FIELD_PRODUCT:
        key = lambda r: (str(r.get("product_code") or ""), *base(r))
    elif sort == SORT_FIELD_TOTAL_VALUE:
        key = lambda r: (_dec(r.get("total_value")), *base(r))
    else:
        key = lambda r: (str(r.get("entry_date") or ""), *base(r))
    return sorted(rows, key=key, reverse=(sort_dir == "desc"))


def _build_summary(rows: list[dict[str, Any]]) -> CostCenterExpenseSummary:
    total = sum((_dec(r.get("total_value")) for r in rows), Decimal("0"))
    documents = {str(r.get("document") or "") for r in rows} - {""}
    suppliers = {
        f"{r.get('supplier_code') or ''}|{r.get('supplier_store') or ''}"
        for r in rows
    } - {"|"}
    finding_count = sum(len(r["findings"]) for r in rows)

    by_cc: dict[str, dict[str, Any]] = {}
    for r in rows:
        cc = (r.get("cost_center") or "").strip()
        bucket = by_cc.setdefault(
            cc or "(sem centro de custo)",
            {"costCenter": cc or None, "lineCount": 0,
             "totalValue": Decimal("0"), "findingCount": 0},
        )
        bucket["lineCount"] += 1
        bucket["totalValue"] += _dec(r.get("total_value"))
        bucket["findingCount"] += len(r["findings"])
        if cc:
            bucket["costCenterDescription"] = (
                r.get("cost_center_description") or None
            )

    by_tp: dict[str, dict[str, Any]] = {}
    for r in rows:
        tp = (r.get("product_type") or "").strip() or "?"
        bucket = by_tp.setdefault(
            tp, {"productType": tp, "lineCount": 0,
                 "totalValue": Decimal("0")}
        )
        bucket["lineCount"] += 1
        bucket["totalValue"] += _dec(r.get("total_value"))

    return CostCenterExpenseSummary(
        totalValue=str(total.quantize(Q2)),
        lineCount=len(rows),
        documentCount=len(documents),
        # Buckets of byCostCenter — the historical artifact counts the
        # «sem centro de custo» group as one of its 46 centers.
        costCenterCount=len(by_cc),
        supplierCount=len(suppliers),
        findingCount=finding_count,
        unclassifiedCount=len(rows),
        byCostCenter=[
            {**b, "totalValue": str(b["totalValue"].quantize(Q2))}
            for b in sorted(
                by_cc.values(),
                key=lambda b: (-b["totalValue"], str(b["costCenter"])),
            )
        ],
        byProductType=[
            {**b, "totalValue": str(b["totalValue"].quantize(Q2))}
            for b in sorted(
                by_tp.values(), key=lambda b: -b["totalValue"]
            )
        ],
    )


def _selection_block(request: CostCenterExpensesRequest) -> dict[str, Any]:
    return {
        "axis": "D1_DTDIGIT",
        "grain": "sd1_item",
        "excludedTes": list(EXCLUDED_TES),
        "excludeMp": True,
        "excludeBenefits": True,
        "benefitPredicate": (
            "TES=046 AND type=GG AND group=4100 AND no cost center"
        ),
        "universe": request.universe,
        "universeSemantics": (
            "calculation=official selection; investigation=in-competence "
            "rows outside the official selection — totals never combined"
        ),
        "tesExclusionEvidence": (
            "observed 13-TES set that reproduces the artifact; the "
            "narrated 12-TES count remains a documented residual "
            "(doc 126 §19)"
        ),
        "historicalBaseline": _PARITY_BASELINE,
    }


def _to_item(
    row: dict[str, Any], *, universe: str
) -> CostCenterExpenseItem:
    total = _dec(row.get("total_value")).quantize(Q2)
    quantity = _dec(row.get("quantity")).quantize(Q6)
    unit = _dec(row.get("unit_value")).quantize(Q6)
    return CostCenterExpenseItem(
        lineId=int(row.get("line_id") or 0),
        branchCode=row.get("branch_code") or "",
        document=row.get("document") or "",
        series=row.get("series") or None,
        item=row.get("item") or None,
        sequence=row.get("sequence_number") or None,
        productCode=row.get("product_code") or "",
        productDescription=row.get("product_description") or None,
        productType=row.get("product_type") or None,
        productGroup=row.get("product_group") or None,
        documentType=row.get("document_type") or None,
        costCenter=(row.get("cost_center") or "").strip() or None,
        costCenterDescription=row.get("cost_center_description") or None,
        accountCode=row.get("account_code") or None,
        tes=row.get("tes") or None,
        cf=row.get("cf") or None,
        supplierCode=row.get("supplier_code") or None,
        supplierStore=row.get("supplier_store") or None,
        supplierName=row.get("supplier_name") or None,
        warehouse=row.get("warehouse") or None,
        orderNumber=row.get("order_number") or None,
        entryDate=row.get("entry_date") or "",
        issueDate=row.get("issue_date") or None,
        quantity=str(quantity),
        unitValue=str(unit),
        totalValue=str(total),
        universe=universe,
        calculationExclusion=row.get("calculation_exclusion"),
        costClass=COST_CLASS_UNCLASSIFIED,
        costCenterCatalogStatus=row.get("cc_catalog_status") or "",
        findings=[f["ruleId"] for f in row.get("findings") or []],
    )
