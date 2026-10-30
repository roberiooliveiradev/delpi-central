"""R11 billing-exclusion roster query (doc 126 §§16.2/17, stage-02).

Investigative review list — NOT a calculation. The roster reproduces
the observed historical selection (axis ``D2_EMISSAO``,
``D2_GRUPO='9035' AND D2_TES='594'``): 11 SD2 item lines /
R$ 97.462,71 / 11 documents for 2026-09/01 (parity baseline recorded in
``selection``).

- ``candidates``    — lines matching the observed historical criteria;
- ``out_of_criteria`` — in-competence lines related to the criteria
  (group 9035 XOR TES 594, DV-R11-04) returned with their own totals;
- ``all``           — both populations, each total kept separate.

Membership never means confirmed error and nothing is excluded
automatically from CPV, billing or DRE (D-02). While E11a/E11b remain
pending, the response carries ``affectedCalculation=TO_INVENTORY`` and
never prescribes a corrective action.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.financeiro_billing_exclusion_roster.billing_exclusion_roster_request import (
    BillingExclusionRosterRequest,
)
from app.application.dto.financeiro_billing_exclusion_roster.billing_exclusion_roster_response import (
    BillingExclusionFinding,
    BillingExclusionItem,
    BillingExclusionRosterResponse,
    BillingExclusionSummary,
)
from app.application.dto.financeiro_billing_exclusion_roster.constantes import (
    COST_STATUS_STRUCTURAL_ZERO,
    FINDINGS_CAP,
    REPORT_ID,
    ROSTER_PRODUCT_GROUP,
    ROSTER_TES,
    RULE_HISTORICAL_SELECTION,
    RULE_MISSING_STOCK_SIBLING,
    RULE_RELATED_OUT_OF_CRITERIA,
    RULE_STRUCTURAL_ZERO_COST,
    SELECTION_MATCHES,
    SELECTION_OUT_OF_CRITERIA,
    SORT_FIELD_DATE,
    SORT_FIELD_DOCUMENT,
    SORT_FIELD_PRODUCT,
    SORT_FIELD_TOTAL_VALUE,
    VIEW_ALL,
    VIEW_CANDIDATES,
    VIEW_OUT_OF_CRITERIA,
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
from app.domain.ports.financeiro_billing_exclusion_roster.billing_exclusion_roster_repository_port import (
    BillingExclusionRosterRepositoryPort,
)

from ._findings import evaluate_findings, line_cost_status

Q2 = Decimal("0.01")
Q6 = Decimal("0.000001")

_ENGINE_ID = "r11-billing-exclusion-roster-v1"
_OFFICIAL_PRODUCER = "EDAPP"

# Parity baseline reproduced live on 2026-09 / branch 01 (evidence:
# 11 SD2 item lines, R$ 97.462,71, 11 documents, 3 documents without a
# stock-moving sibling item — identical to NF a desconsiderar.xlsb /
# Planilha2, doc 126 §2, doc 85 BR-R11-001/004).
_PARITY_BASELINE = {
    "period": "2026-09",
    "branch": "01",
    "lineCount": 11,
    "totalValue": "97462.71",
    "documentCount": 11,
    "missingStockSiblingDocumentCount": 3,
    "artifact": "NF a desconsiderar.xlsb / Planilha2",
    "status": "PROVEN",
}

_RULES_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "ruleId": RULE_HISTORICAL_SELECTION,
        "description": (
            "Seleção investigativa: grupo 9035 ∩ TES 594 na competência "
            "e filial — critério observado no artefato histórico."
        ),
        "implemented": True,
        "kind": "selection",
        "limitation": (
            "E11b — o artefato não distingue se o operador filtrou "
            "grupo, TES ou a interseção; o predicado não é regra "
            "oficial universal."
        ),
        "evidenceRefs": ["doc-126#DV-R11-01", "doc-85#BR-R11-002"],
    },
    {
        "ruleId": RULE_STRUCTURAL_ZERO_COST,
        "description": (
            "Custo de estoque estruturalmente zero: TES com "
            "F4_ESTOQUE='N' não gera D2_CUSTO1 — condição esperada que "
            "explica a ausência no CPV, não divergência."
        ),
        "implemented": True,
        "kind": "explanation",
        "expressedAs": "item.costStatus",
        "evidenceRefs": ["doc-126#DV-R11-02", "doc-85#BR-R11-003"],
    },
    {
        "ruleId": RULE_MISSING_STOCK_SIBLING,
        "description": (
            "Item da seleção cujo documento não possui item-irmão que "
            "movimenta estoque (F4_ESTOQUE='S')."
        ),
        "implemented": True,
        "evidenceRefs": ["doc-126#DV-R11-03", "doc-85#BR-R11-004"],
    },
    {
        "ruleId": RULE_RELATED_OUT_OF_CRITERIA,
        "description": (
            "Linhas relacionadas fora do predicado: grupo 9035 com "
            "outro TES ou TES 594 em outro grupo."
        ),
        "implemented": True,
        "expressedAs": "view=out_of_criteria",
        "note": (
            "Revisão humana — nunca incluídas nos totalizadores da "
            "seleção histórica."
        ),
        "evidenceRefs": ["doc-126#DV-R11-04"],
    },
)

_PENDING_DECISIONS = [
    "E11a — apuração que recebe a desconsideração e ação corretiva no "
    "ERP ainda não comprovadas; orientação limitada a localizar e "
    "conferir o lançamento no Protheus.",
    "E11b — predicado oficial (grupo 9035 vs TES 594 vs interseção) "
    "não decidido; o critério exposto é o observado no artefato.",
]

_PARITY_NOTES = [
    "Consulta investigativa — não é a emissão oficial do relatório "
    "R11; paridade oficial permanece PENDING de homologação humana.",
    "Seleção histórica reproduzida para 2026-09/filial 01: 11 linhas, "
    "R$ 97.462,71, 11 documentos — idêntica ao artefato documentado.",
    "Nenhuma nota é excluída automaticamente de CPV, faturamento ou "
    "DRE — a correção é atividade humana externa no TOTVS/Protheus.",
    *_PENDING_DECISIONS,
]


class ListBillingExclusionRosterUseCase:
    """Lists the R11 roster view with findings."""

    def __init__(
        self,
        *,
        repository: BillingExclusionRosterRepositoryPort,
        scope_resolver: StockInventoryScopeResolver,
    ) -> None:
        self._repository = repository
        self._scope_resolver = scope_resolver

    def execute(
        self,
        request: BillingExclusionRosterRequest,
        *,
        user_subject: str | None,
    ) -> BillingExclusionRosterResponse:
        scope = self._scope_resolver.resolve(user_subject=user_subject)
        if not scope.resolved:
            raise StockInventoryScopeUnavailableError(scope.reason)

        rows = self._repository.fetch_lines(
            period_start=request.period_start(),
            period_end=request.period_end(),
            branches=request.requested_branches(),
            product_group=request.product_group,
            product_code=request.product_code,
            document=request.document,
            customer_code=request.customer_code,
            tes=request.tes,
        )

        enriched: list[dict[str, Any]] = []
        for row in rows:
            row = dict(row)
            row["selection_status"] = _selection_status(row)
            row["cost_status"] = line_cost_status(row)
            row["findings"] = evaluate_findings(row)
            enriched.append(row)

        summary = _build_summary(enriched)

        findings: list[dict[str, Any]] = []
        if request.include_findings:
            for row in enriched:
                findings.extend(row["findings"])
        findings_truncated = len(findings) > FINDINGS_CAP
        if findings_truncated:
            findings = findings[:FINDINGS_CAP]

        view_rows = _apply_view(enriched, view=request.view)
        view_rows = _sort_rows(
            view_rows, sort=request.sort, sort_dir=request.sort_dir
        )

        total_items = len(view_rows)
        offset = (request.page - 1) * request.page_size
        page_rows = view_rows[offset : offset + request.page_size]

        return BillingExclusionRosterResponse(
            report=REPORT_ID,
            period=request.period,
            branchCode=request.branch,
            view=request.view,
            status=(
                STATUS_AVAILABLE if total_items else STATUS_NO_MATCHING_ITEMS
            ),
            selection=_selection_block(request),
            pagination={
                "page": request.page,
                "page_size": request.page_size,
                "total_items": total_items,
                "population_items": len(enriched),
            },
            summary=summary,
            findings=[
                BillingExclusionFinding(
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
                "sourceTables": "SD2010+SF4010+SB1010+SA1010",
                "artifact": "NF a desconsiderar.xlsb / Planilha2",
                "periodStart": request.period_start(),
                "periodEnd": request.period_end(),
                "affectedCalculation": "TO_INVENTORY",
                "correctiveAction": "PENDING_EVIDENCE",
            },
            items=[_to_item(r) for r in page_rows],
        )


def _selection_status(row: dict[str, Any]) -> str:
    """DV-R11-01 — the observed historical predicate."""
    matches = (
        (row.get("product_group") or "").strip() == ROSTER_PRODUCT_GROUP
        and (row.get("tes") or "").strip() == ROSTER_TES
    )
    return SELECTION_MATCHES if matches else SELECTION_OUT_OF_CRITERIA


def _apply_view(
    rows: list[dict[str, Any]], *, view: str
) -> list[dict[str, Any]]:
    if view == VIEW_CANDIDATES:
        return [
            r for r in rows if r["selection_status"] == SELECTION_MATCHES
        ]
    if view == VIEW_OUT_OF_CRITERIA:
        return [
            r
            for r in rows
            if r["selection_status"] == SELECTION_OUT_OF_CRITERIA
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
            str(row.get("series") or ""),
            str(row.get("item") or ""),
            int(row.get("line_id") or 0),
        )

    if sort == SORT_FIELD_DATE:
        key = lambda r: (str(r.get("issue_date") or ""), *base(r))
    elif sort == SORT_FIELD_DOCUMENT:
        key = lambda r: base(r)
    elif sort == SORT_FIELD_PRODUCT:
        key = lambda r: (str(r.get("product_code") or ""), *base(r))
    elif sort == SORT_FIELD_TOTAL_VALUE:
        key = lambda r: (_dec(r.get("total_value")), *base(r))
    else:
        key = lambda r: (str(r.get("issue_date") or ""), *base(r))
    return sorted(rows, key=key, reverse=(sort_dir == "desc"))


def _build_summary(
    rows: list[dict[str, Any]],
) -> BillingExclusionSummary:
    """Totals over the FULL authorized population — each selection
    population counted separately, never blended."""
    total = sum((_dec(r.get("total_value")) for r in rows), Decimal("0"))
    documents = {str(r.get("document") or "") for r in rows} - {""}
    customers = {
        f"{r.get('customer_code') or ''}|{r.get('customer_store') or ''}"
        for r in rows
    } - {"|"}
    finding_count = sum(len(r["findings"]) for r in rows)
    zero_cost = sum(
        1 for r in rows if r["cost_status"] == COST_STATUS_STRUCTURAL_ZERO
    )
    missing_sibling_docs = {
        str(r.get("document") or "")
        for r in rows
        if r["selection_status"] == SELECTION_MATCHES
        and not r.get("has_stock_sibling_item")
    } - {""}

    by_tes: dict[str, dict[str, Any]] = {}
    for r in rows:
        tes = (r.get("tes") or "").strip() or "?"
        bucket = by_tes.setdefault(
            tes,
            {"tes": tes, "lineCount": 0, "totalValue": Decimal("0")},
        )
        bucket["lineCount"] += 1
        bucket["totalValue"] += _dec(r.get("total_value"))

    by_group: dict[str, dict[str, Any]] = {}
    for r in rows:
        grp = (r.get("product_group") or "").strip() or "?"
        bucket = by_group.setdefault(
            grp,
            {"productGroup": grp, "lineCount": 0,
             "totalValue": Decimal("0")},
        )
        bucket["lineCount"] += 1
        bucket["totalValue"] += _dec(r.get("total_value"))

    return BillingExclusionSummary(
        totalValue=str(total.quantize(Q2)),
        lineCount=len(rows),
        documentCount=len(documents),
        customerCount=len(customers),
        zeroCostCount=zero_cost,
        missingStockSiblingDocumentCount=len(missing_sibling_docs),
        findingCount=finding_count,
        candidateLineCount=sum(
            1
            for r in rows
            if r["selection_status"] == SELECTION_MATCHES
        ),
        outOfCriteriaLineCount=sum(
            1
            for r in rows
            if r["selection_status"] == SELECTION_OUT_OF_CRITERIA
        ),
        byTes=[
            {**b, "totalValue": str(b["totalValue"].quantize(Q2))}
            for b in sorted(
                by_tes.values(), key=lambda b: -b["totalValue"]
            )
        ],
        byProductGroup=[
            {**b, "totalValue": str(b["totalValue"].quantize(Q2))}
            for b in sorted(
                by_group.values(), key=lambda b: -b["totalValue"]
            )
        ],
    )


def _selection_block(
    request: BillingExclusionRosterRequest,
) -> dict[str, Any]:
    return {
        "axis": "D2_EMISSAO",
        "grain": "sd2_item",
        "observedCriteria": {
            "productGroup": ROSTER_PRODUCT_GROUP,
            "tes": ROSTER_TES,
        },
        "view": request.view,
        "viewSemantics": (
            "candidates=matches the observed historical criteria; "
            "out_of_criteria=related rows (group 9035 XOR TES 594); "
            "all=both populations with separate totals — never blended"
        ),
        "predicateOfficiality": (
            "TO_INVENTORY (E11b) — the artifact does not reveal whether "
            "the operator filtered group, TES or the intersection; the "
            "observed predicate is evidence, not a universal rule"
        ),
        "affectedCalculation": (
            "TO_INVENTORY (E11a) — which calculation the exclusion "
            "feeds and the corrective ERP action are unproven; nothing "
            "is excluded automatically"
        ),
        "historicalBaseline": _PARITY_BASELINE,
    }


def _to_item(row: dict[str, Any]) -> BillingExclusionItem:
    total = _dec(row.get("total_value")).quantize(Q2)
    quantity = _dec(row.get("quantity")).quantize(Q6)
    unit = _dec(row.get("unit_price")).quantize(Q6)
    stock_cost = _dec(row.get("stock_cost")).quantize(Q2)
    return BillingExclusionItem(
        lineId=int(row.get("line_id") or 0),
        branchCode=row.get("branch_code") or "",
        document=row.get("document") or "",
        series=row.get("series") or None,
        item=row.get("item") or None,
        productCode=row.get("product_code") or "",
        productDescription=row.get("product_description") or None,
        productType=row.get("product_type") or None,
        productGroup=row.get("product_group") or None,
        tes=row.get("tes") or None,
        tesDescription=row.get("tes_description") or None,
        cf=row.get("cf") or None,
        customerCode=row.get("customer_code") or None,
        customerStore=row.get("customer_store") or None,
        customerName=row.get("customer_name") or None,
        accountCode=row.get("account_code") or None,
        warehouse=row.get("warehouse") or None,
        orderNumber=row.get("order_number") or None,
        issueDate=row.get("issue_date") or "",
        quantity=str(quantity),
        unitPrice=str(unit),
        totalValue=str(total),
        stockCost=str(stock_cost),
        tesStockMovement=row.get("tes_stock_movement") or None,
        tesDuplicateFlag=row.get("tes_duplicate_flag") or None,
        documentItemCount=int(row.get("document_item_count") or 0),
        hasStockSiblingItem=bool(row.get("has_stock_sibling_item")),
        selectionStatus=row.get("selection_status") or "",
        costStatus=row.get("cost_status") or "",
        findings=[f["ruleId"] for f in row.get("findings") or []],
    )
