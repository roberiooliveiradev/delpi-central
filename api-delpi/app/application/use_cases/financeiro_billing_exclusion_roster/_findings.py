"""Divergence-rule evaluation for R11 (doc 126 §16.2).

Every evaluator receives a normalized SD2 row and returns zero or more
``POSSIBLE_DIVERGENCE`` findings — never ``CONFIRMED_ERROR``.

Implemented subset (evidence-backed):
- DV-R11-03  roster line whose document carries no stock-moving sibling
  item (``F4_ESTOQUE='S'``) — the historical artifact had 3 of 11; an
  unusual shape worth human review, never proof of error.

Explanatory / selection rules — expressed elsewhere, not as findings:
- DV-R11-01  the roster selection itself (``selection`` block);
- DV-R11-02  ``D2_CUSTO1=0`` with ``F4_ESTOQUE='N'`` is the EXPECTED
  structural condition (doc 85 BR-R11-003) — exposed as the item
  ``costStatus``, never a divergence;
- DV-R11-04  related rows outside the criteria are returned by the
  ``out_of_criteria`` view — candidates for human review, not findings.

While E11a/E11b remain pending, no rule may state which calculation is
affected or prescribe a corrective action in the ERP.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_billing_exclusion_roster.constantes import (
    COST_STATUS_STANDARD,
    COST_STATUS_STRUCTURAL_ZERO,
    FINDING_POSSIBLE_DIVERGENCE,
    RULE_MISSING_STOCK_SIBLING,
    SELECTION_MATCHES,
)

_GUIDANCE_PREFIX = (
    "Conferir no Protheus o documento e o item da SD2 (faturamento) "
)
_EVIDENCE_BASE = ["doc-85#BR-R11-001", "doc-126#16.2"]


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


def line_cost_status(row: dict[str, Any]) -> str:
    """DV-R11-02 — zero cost with a non-stock TES is structural."""
    stock_cost = row.get("stock_cost")
    stock_movement = (row.get("tes_stock_movement") or "").strip()
    try:
        zero_cost = float(stock_cost or 0) == 0.0
    except (TypeError, ValueError):
        zero_cost = False
    if zero_cost and stock_movement == "N":
        return COST_STATUS_STRUCTURAL_ZERO
    return COST_STATUS_STANDARD


def evaluate_findings(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the implemented DV-R11 subset over one normalized row.

    Findings are only emitted for roster candidates — related
    out-of-criteria rows already carry ``selectionStatus`` marking
    them as review material (DV-R11-04) without alleging divergence.
    """
    findings: list[dict[str, Any]] = []
    if row.get("selection_status") != SELECTION_MATCHES:
        return findings

    line_id = int(row.get("line_id") or 0)
    source = _source_record(row)

    if not row.get("has_stock_sibling_item"):
        findings.append(
            _new_finding(
                rule_id=RULE_MISSING_STOCK_SIBLING,
                line_id=line_id,
                source_record=source,
                observed={
                    "document": row.get("document"),
                    "series": row.get("series"),
                    "documentItemCount": row.get("document_item_count"),
                    "tes": row.get("tes"),
                    "productCode": row.get("product_code"),
                    "productGroup": row.get("product_group"),
                    "cf": row.get("cf"),
                },
                explanation=(
                    "Documento da seleção histórica sem item-irmão que "
                    "movimente estoque (F4_ESTOQUE='S'). Nas NFs típicas "
                    "do artefato, o item TES 594 acompanha um item "
                    "físico (ex.: TES 510) — a ausência é uma situação "
                    "que merece conferência, não erro comprovado."
                ),
                guidance=_GUIDANCE_PREFIX
                + "e verificar se o documento deveria conter um item "
                "de produto físico; a decisão de desconsiderar e a "
                "apuração afetada dependem de regra funcional ainda não "
                "homologada (E11a/E11b).",
                evidence_refs=[
                    *_EVIDENCE_BASE,
                    "doc-126#DV-R11-03",
                    "doc-85#BR-R11-004",
                ],
            )
        )
    return findings


def _source_record(row: dict[str, Any]) -> dict[str, Any]:
    """ERP references needed to locate the SD2 line in Protheus."""
    return {
        "document": row.get("document"),
        "series": row.get("series"),
        "item": row.get("item"),
        "sequence": row.get("sequence_number"),
        "productCode": row.get("product_code"),
        "productType": row.get("product_type"),
        "productGroup": row.get("product_group"),
        "accountCode": row.get("account_code"),
        "tes": row.get("tes"),
        "cf": row.get("cf"),
        "customerCode": row.get("customer_code"),
        "store": row.get("customer_store"),
        "branch": row.get("branch_code"),
        "warehouse": row.get("warehouse"),
        "orderNumber": row.get("order_number"),
        "issueDate": row.get("issue_date"),
        "quantity": row.get("quantity"),
        "unitPrice": row.get("unit_price"),
        "totalValue": row.get("total_value"),
        "stockCost": row.get("stock_cost"),
    }
