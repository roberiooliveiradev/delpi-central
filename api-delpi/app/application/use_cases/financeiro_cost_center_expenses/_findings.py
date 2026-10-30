"""Divergence-rule evaluation for R10 (doc 126 §16.1).

Every evaluator receives a normalized SD1 row and returns zero or more
``POSSIBLE_DIVERGENCE`` findings — never ``CONFIRMED_ERROR``. Rules
blocked by the pending E10a catalog (DV-R10-03, DV-R10-06) are declared
in the response ``rulesCatalog`` and produce no findings: no prefix
heuristics, no inferred incompatibility.

Implemented subset (evidence-backed):
- DV-R10-01  raw material (``D1_TP='MP'``) carrying a cost center —
  evaluated in the investigation universe, where MP rows live;
- DV-R10-02  cost center absent from the current CTT analytic catalog,
  synthetic, or blocked — honest wording: catalog validity is the
  CURRENT snapshot, not proof about the historical competence;
- DV-R10-04  expense line without cost center;
- DV-R10-05  cost class status — every row is ``UNCLASSIFIED`` (D-01);
  expressed on the item, not as a per-row finding.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_cost_center_expenses.constantes import (
    FINDING_POSSIBLE_DIVERGENCE,
    RULE_COST_CENTER_NOT_IN_CATALOG,
    RULE_MISSING_COST_CENTER,
    RULE_MP_WITH_COST_CENTER,
    UNIVERSE_INVESTIGATION,
)

# CTT register states (CTT_CLASSE / CTT_BLOQ — Protheus: '1' synthetic
# or blocked, '2' analytic or not blocked).
_CTT_CLASS_SYNTHETIC = "1"
_CTT_CLASS_ANALYTIC = "2"
_CTT_BLOCKED = "1"

CC_STATUS_NOT_APPLICABLE = "not_applicable"
CC_STATUS_ANALYTIC = "registered_analytic"
CC_STATUS_SYNTHETIC = "registered_synthetic"
CC_STATUS_BLOCKED = "registered_blocked"
CC_STATUS_NOT_REGISTERED = "not_registered"

_GUIDANCE_PREFIX = (
    "Conferir no Protheus o documento e o item da SD1 (compra/entrada) "
)
_EVIDENCE_BASE = ["doc-85#BR-R10-001", "doc-126#16.1"]


def _new_finding(
    *,
    rule_id: str,
    line_id: int,
    source_record: dict[str, Any],
    observed: dict[str, Any],
    explanation: str,
    guidance: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "status": FINDING_POSSIBLE_DIVERGENCE,
        "lineId": line_id,
        "sourceRecord": source_record,
        "observedValues": observed,
        "findingExplanation": explanation,
        "evidenceRefs": evidence_refs or list(_EVIDENCE_BASE),
        "erpReviewGuidance": guidance,
    }


def cost_center_catalog_status(row: dict[str, Any]) -> str:
    """CTT register state for the line's cost center (current snapshot)."""
    cc = (row.get("cost_center") or "").strip()
    if not cc:
        return CC_STATUS_NOT_APPLICABLE
    class_kind = (row.get("cost_center_class_kind") or "").strip()
    blocked = (row.get("cost_center_blocked") or "").strip()
    if not class_kind:
        return CC_STATUS_NOT_REGISTERED
    if class_kind == _CTT_CLASS_SYNTHETIC:
        return CC_STATUS_SYNTHETIC
    if blocked == _CTT_BLOCKED:
        return CC_STATUS_BLOCKED
    if class_kind == _CTT_CLASS_ANALYTIC:
        return CC_STATUS_ANALYTIC
    return CC_STATUS_NOT_REGISTERED


def evaluate_findings(
    row: dict[str, Any], *, universe: str
) -> list[dict[str, Any]]:
    """Run the implemented DV-R10 subset over one normalized row."""
    findings: list[dict[str, Any]] = []
    cc = (row.get("cost_center") or "").strip()
    cc_desc = (row.get("cost_center_description") or "").strip() or None
    product_type = (row.get("product_type") or "").strip()
    line_id = int(row.get("line_id") or 0)
    source = _source_record(row, cc=cc, cc_desc=cc_desc)

    if not cc:
        findings.append(
            _new_finding(
                rule_id=RULE_MISSING_COST_CENTER,
                line_id=line_id,
                source_record=source,
                observed={
                    "costCenter": "",
                    "productCode": row.get("product_code"),
                    "productType": product_type or None,
                    "tes": row.get("tes"),
                },
                explanation=(
                    "Lançamento de despesa sem centro de custo "
                    "preenchido — a ausência pode indicar pendência de "
                    "classificação ou rateio não informado."
                ),
                guidance=_GUIDANCE_PREFIX
                + "e confirmar se o centro de custo deveria ter sido "
                "informado; ajustar a classificação no ERP, se aplicável.",
                evidence_refs=[*_EVIDENCE_BASE, "doc-126#DV-R10-04"],
            )
        )
    else:
        status = cost_center_catalog_status(row)
        if status == CC_STATUS_NOT_REGISTERED:
            findings.append(
                _new_finding(
                    rule_id=RULE_COST_CENTER_NOT_IN_CATALOG,
                    line_id=line_id,
                    source_record=source,
                    observed={
                        "costCenter": cc,
                        "catalogStatus": status,
                        "productCode": row.get("product_code"),
                        "productType": product_type or None,
                        "tes": row.get("tes"),
                    },
                    explanation=(
                        f"Centro de custo '{cc}' não localizado no "
                        "cadastro CTT vigente. O cadastro atual não "
                        "comprova a situação histórica do código na "
                        "competência — é candidato a revisão, não erro "
                        "confirmado."
                    ),
                    guidance=_GUIDANCE_PREFIX
                    + "e verificar no cadastro CTT se o centro de "
                    "custo existe/está ativo para a competência.",
                    evidence_refs=[*_EVIDENCE_BASE, "doc-126#DV-R10-02"],
                )
            )
        elif status == CC_STATUS_SYNTHETIC:
            findings.append(
                _new_finding(
                    rule_id=RULE_COST_CENTER_NOT_IN_CATALOG,
                    line_id=line_id,
                    source_record=source,
                    observed={
                        "costCenter": cc,
                        "catalogStatus": status,
                        "costCenterDescription": cc_desc,
                        "tes": row.get("tes"),
                    },
                    explanation=(
                        f"Centro de custo '{cc}' consta como sintético "
                        "no cadastro CTT vigente — contas sintéticas não "
                        "deveriam receber lançamentos analíticos."
                    ),
                    guidance=_GUIDANCE_PREFIX
                    + "e conferir no cadastro CTT a classe do centro de "
                    "custo utilizado.",
                    evidence_refs=[*_EVIDENCE_BASE, "doc-126#DV-R10-02"],
                )
            )
        elif status == CC_STATUS_BLOCKED:
            findings.append(
                _new_finding(
                    rule_id=RULE_COST_CENTER_NOT_IN_CATALOG,
                    line_id=line_id,
                    source_record=source,
                    observed={
                        "costCenter": cc,
                        "catalogStatus": status,
                        "costCenterDescription": cc_desc,
                        "tes": row.get("tes"),
                    },
                    explanation=(
                        f"Centro de custo '{cc}' consta bloqueado no "
                        "cadastro CTT vigente. O bloqueio atual não "
                        "comprova a situação histórica — candidato a "
                        "revisão, não erro confirmado."
                    ),
                    guidance=_GUIDANCE_PREFIX
                    + "e conferir no cadastro CTT a vigência/bloqueio "
                    "do centro de custo.",
                    evidence_refs=[*_EVIDENCE_BASE, "doc-126#DV-R10-02"],
                )
            )

    if (
        universe == UNIVERSE_INVESTIGATION
        and product_type == "MP"
        and cc
    ):
        findings.append(
            _new_finding(
                rule_id=RULE_MP_WITH_COST_CENTER,
                line_id=line_id,
                source_record=source,
                observed={
                    "costCenter": cc,
                    "costCenterDescription": cc_desc,
                    "productCode": row.get("product_code"),
                    "productType": product_type,
                    "productGroup": row.get("product_group"),
                    "tes": row.get("tes"),
                },
                explanation=(
                    "Item de matéria-prima (tipo MP) com centro de "
                    "custo atribuído — fora do universo da apuração de "
                    "despesas, mas potencial contaminação de rateio: "
                    "a classificação esperada depende do catálogo "
                    "CC→classe ainda não homologado (E10a)."
                ),
                guidance=_GUIDANCE_PREFIX
                + "e conferir se a matéria-prima deveria carregar esse "
                "centro de custo ou se o rateio foi indevido.",
                evidence_refs=[
                    *_EVIDENCE_BASE,
                    "doc-126#DV-R10-01",
                    "doc-56#50:35",
                ],
            )
        )
    return findings


def _source_record(
    row: dict[str, Any], *, cc: str, cc_desc: str | None
) -> dict[str, Any]:
    """ERP references needed to locate the SD1 line in Protheus."""
    return {
        "document": row.get("document"),
        "series": row.get("series"),
        "item": row.get("item"),
        "sequence": row.get("sequence_number"),
        "productCode": row.get("product_code"),
        "productType": row.get("product_type"),
        "costCenterCode": cc or None,
        "costCenterDescription": cc_desc,
        "accountCode": row.get("account_code"),
        "tes": row.get("tes"),
        "cf": row.get("cf"),
        "supplierCode": row.get("supplier_code"),
        "store": row.get("supplier_store"),
        "branch": row.get("branch_code"),
        "warehouse": row.get("warehouse"),
        "orderNumber": row.get("order_number"),
        "entryDate": row.get("entry_date"),
        "issueDate": row.get("issue_date"),
        "quantity": row.get("quantity"),
        "totalValue": row.get("total_value"),
    }
