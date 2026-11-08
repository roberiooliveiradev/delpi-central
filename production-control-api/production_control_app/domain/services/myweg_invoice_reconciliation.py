"""Conciliação analítica MyWEG necessidades × NF portal — sem baixa transacional.

Necessidade atual já incorpora abatimentos da WEG: nunca descontar NF novamente.
Chave de conciliação: material WEG (não productKey DELPI).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

from production_control_app.domain.myweg_invoice_observations_contract import (
    OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
    OBSERVATION_STATUS_WITH_RECORDS,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_comparison import (
    resolve_product_identity,
    ZERO,
)

COVERAGE_COMPLETE = "complete"
COVERAGE_PARTIAL = "partial"
COVERAGE_CONFLICT = "conflict"
COVERAGE_UNAVAILABLE = "unavailable"
COVERAGE_PENDING_INGESTION = "pending_invoice_ingestion"

MATCH_OK = "reconciled"
MATCH_NONE = "none"
MATCH_AMBIGUOUS = "ambiguous_identity"
MATCH_SHARED = "attributed_elsewhere"
MATCH_MULTI_MATERIAL = "multi_material_key"
MATCH_UNAVAILABLE = "unavailable"
MATCH_PARTIAL = "partial_coverage"
MATCH_CONFLICT = "conflict"

MANAGERIAL_INVOICED = "invoiced"
MANAGERIAL_PARTIAL = "partial_invoicing"
MANAGERIAL_INVESTIGATE = "reduction_to_investigate"
MANAGERIAL_PENDING = "reconciliation_pending"
MANAGERIAL_OTHER = "other_movement"

MANAGERIAL_PENDING_MATCHES = frozenset(
    {
        MATCH_AMBIGUOUS,
        MATCH_SHARED,
        MATCH_MULTI_MATERIAL,
        MATCH_PARTIAL,
        MATCH_CONFLICT,
        MATCH_UNAVAILABLE,
    }
)

_ZERO = ZERO


@dataclass(frozen=True)
class InvoiceWindow:
    start: date
    end: date  # inclusive
    days: tuple[date, ...]
    status: str  # ok | same_day | invalid_order | empty
    reason: str | None = None


@dataclass(frozen=True)
class CanonicalDaySelection:
    document_date: date
    status: str  # selected | empty_signaled | conflict | missing
    observation_id: str | None = None
    collection_id: str | None = None
    semantic_sha256: str | None = None
    payload_sha256: str | None = None
    observation_status: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class MaterialReconciliation:
    material_weg: str
    previous_need_un: Decimal
    current_need_un: Decimal
    observed_delta_un: Decimal
    posted_nf_un: Decimal
    adjusted_planning_delta_un: Decimal | None
    compatible_reduction_un: Decimal | None
    invoice_match_status: str
    source_observation_ids: tuple[str, ...]


def build_invoice_window(*, from_date: date, to_date: date) -> InvoiceWindow:
    """Janela fiscal inicial: [from, to - 1 dia] em datas de coleta."""
    if to_date < from_date:
        return InvoiceWindow(
            start=from_date,
            end=from_date,
            days=(),
            status="invalid_order",
            reason="collection_date(to) anterior a collection_date(from).",
        )
    if to_date == from_date:
        return InvoiceWindow(
            start=from_date,
            end=from_date,
            days=(),
            status="same_day",
            reason="Par na mesma data operacional — janela fiscal vazia.",
        )
    end = to_date - timedelta(days=1)
    if end < from_date:
        return InvoiceWindow(
            start=from_date,
            end=end,
            days=(),
            status="empty",
            reason="Cutoff insuficiente para formar janela.",
        )
    days: list[date] = []
    cursor = from_date
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return InvoiceWindow(start=from_date, end=end, days=tuple(days), status="ok")


def select_canonical_observation_for_day(
    observations: Sequence[Mapping[str, Any]],
    *,
    document_date: date,
) -> CanonicalDaySelection:
    """Seleção determinística diária — equivalentes por semantic_sha256 não somam."""
    scoped = [
        row
        for row in observations
        if _as_date(row.get("document_date")) == document_date
    ]
    if not scoped:
        return CanonicalDaySelection(
            document_date=document_date,
            status="missing",
            reason="Nenhuma observação importada para a data.",
        )

    by_semantic: dict[str, list[Mapping[str, Any]]] = {}
    for row in scoped:
        semantic = str(row.get("semantic_sha256") or "").strip().lower()
        if not semantic:
            return CanonicalDaySelection(
                document_date=document_date,
                status="conflict",
                reason="Observação sem semantic_sha256.",
            )
        by_semantic.setdefault(semantic, []).append(row)

    if len(by_semantic) > 1:
        return CanonicalDaySelection(
            document_date=document_date,
            status="conflict",
            reason=(
                f"Observações contraditórias na data "
                f"({len(by_semantic)} semantic_sha256 distintos)."
            ),
        )

    group = next(iter(by_semantic.values()))
    chosen = _pick_deterministic(group)
    obs_status = str(chosen.get("observation_status") or "").strip()
    if obs_status == OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP:
        status = "empty_signaled"
    elif obs_status == OBSERVATION_STATUS_WITH_RECORDS:
        status = "selected"
    else:
        return CanonicalDaySelection(
            document_date=document_date,
            status="conflict",
            reason=f"observation_status inválido: {obs_status!r}.",
        )
    return CanonicalDaySelection(
        document_date=document_date,
        status=status,
        observation_id=str(chosen.get("id") or "") or None,
        collection_id=str(chosen.get("collection_id") or "") or None,
        semantic_sha256=str(chosen.get("semantic_sha256") or "").lower() or None,
        payload_sha256=str(chosen.get("payload_sha256") or "").lower() or None,
        observation_status=obs_status,
    )


def evaluate_window_coverage(
    selections: Sequence[CanonicalDaySelection],
) -> dict[str, Any]:
    covered: list[str] = []
    missing: list[str] = []
    conflicts: list[dict[str, str]] = []
    for selection in selections:
        day = selection.document_date.isoformat()
        if selection.status in {"selected", "empty_signaled"}:
            covered.append(day)
        elif selection.status == "missing":
            missing.append(day)
        elif selection.status == "conflict":
            conflicts.append({"documentDate": day, "reason": selection.reason or ""})
        else:
            conflicts.append(
                {
                    "documentDate": day,
                    "reason": selection.reason or selection.status,
                }
            )

    if conflicts:
        status = COVERAGE_CONFLICT
    elif missing and not covered:
        status = COVERAGE_PENDING_INGESTION
    elif missing:
        status = COVERAGE_PARTIAL
    else:
        status = COVERAGE_COMPLETE

    return {
        "status": status,
        "coveredDates": covered,
        "missingDates": missing,
        "conflicts": conflicts,
        "dayCount": len(selections),
        "coveredDayCount": len(covered),
        "missingDayCount": len(missing),
        "conflictDayCount": len(conflicts),
    }


def aggregate_need_quantity_by_material(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        material = str(row.get("material_weg_tratado") or "").strip()
        if not material:
            continue
        qty = _dec(row.get("quantidade_original_un"))
        totals[material] = totals.get(material, _ZERO) + qty
    return totals


def materials_by_product_key(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for row in rows:
        material = str(row.get("material_weg_tratado") or "").strip()
        if not material:
            continue
        product_key, _kind, _verified = resolve_product_identity(row)
        mapping.setdefault(product_key, set()).add(material)
    return mapping


def aggregate_posted_nf_by_material(
    items: Sequence[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Soma quantity_un por material; rejeita itens não comparáveis no caller via flag."""
    totals: dict[str, Decimal] = {}
    for item in items:
        comparability = str(
            item.get("unit_comparability") or item.get("unitComparability") or ""
        ).strip()
        if comparability and comparability != "comparable":
            raise ValueError("non_comparable_unit")
        material = str(
            item.get("material_weg") or item.get("materialWeg") or ""
        ).strip()
        if not material:
            continue
        qty = item.get("quantity_un")
        if qty is None:
            qty = item.get("quantityUn")
        totals[material] = totals.get(material, _ZERO) + _dec(qty)
    return totals


def reconcile_material(
    *,
    material_weg: str,
    previous_need_un: Decimal,
    current_need_un: Decimal,
    posted_nf_un: Decimal,
    coverage_status: str,
    source_observation_ids: Sequence[str],
) -> MaterialReconciliation:
    observed = current_need_un - previous_need_un
    if coverage_status != COVERAGE_COMPLETE:
        status = {
            COVERAGE_PARTIAL: MATCH_PARTIAL,
            COVERAGE_CONFLICT: MATCH_CONFLICT,
            COVERAGE_PENDING_INGESTION: MATCH_UNAVAILABLE,
            COVERAGE_UNAVAILABLE: MATCH_UNAVAILABLE,
        }.get(coverage_status, MATCH_UNAVAILABLE)
        return MaterialReconciliation(
            material_weg=material_weg,
            previous_need_un=previous_need_un,
            current_need_un=current_need_un,
            observed_delta_un=observed,
            posted_nf_un=posted_nf_un if coverage_status == COVERAGE_COMPLETE else _ZERO,
            adjusted_planning_delta_un=None,
            compatible_reduction_un=None,
            invoice_match_status=status,
            source_observation_ids=tuple(source_observation_ids),
        )

    adjusted = observed + posted_nf_un
    compatible = min(max(-observed, _ZERO), posted_nf_un)
    return MaterialReconciliation(
        material_weg=material_weg,
        previous_need_un=previous_need_un,
        current_need_un=current_need_un,
        observed_delta_un=observed,
        posted_nf_un=posted_nf_un,
        adjusted_planning_delta_un=adjusted,
        compatible_reduction_un=compatible,
        invoice_match_status=MATCH_OK if posted_nf_un != _ZERO or observed != _ZERO else MATCH_NONE,
        source_observation_ids=tuple(source_observation_ids),
    )


def assign_materials_to_product_keys(
    *,
    materials: Sequence[str],
    materials_by_key: Mapping[str, set[str]],
    products: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Atribui cada material WEG a exatamente um productKey (sem duplicar NF)."""
    products_by_key = {str(p.get("productKey") or ""): p for p in products}
    assignment: dict[str, str] = {}
    for material in materials:
        candidates = [
            key
            for key, mats in materials_by_key.items()
            if material in mats and key in products_by_key
        ]
        if not candidates:
            # Produto pode expor materialWegTratado sem estar no mapa de linhas
            for key, product in products_by_key.items():
                if str(product.get("materialWegTratado") or "").strip() == material:
                    candidates.append(key)
        if not candidates:
            continue
        preferred = _prefer_product_key(material, candidates, products_by_key)
        assignment[material] = preferred
    return assignment


def enrich_products_with_portal_invoices(
    products: Sequence[Mapping[str, Any]],
    *,
    reconciliations: Mapping[str, MaterialReconciliation],
    materials_by_key: Mapping[str, set[str]],
    coverage_status: str,
) -> list[dict[str, Any]]:
    all_materials = sorted(
        set(reconciliations.keys())
        | {m for mats in materials_by_key.values() for m in mats}
        | {
            str(p.get("materialWegTratado") or "").strip()
            for p in products
            if str(p.get("materialWegTratado") or "").strip()
        }
    )
    assignment = assign_materials_to_product_keys(
        materials=all_materials,
        materials_by_key=materials_by_key,
        products=products,
    )
    inverse: dict[str, list[str]] = {}
    for material, product_key in assignment.items():
        inverse.setdefault(product_key, []).append(material)

    enriched: list[dict[str, Any]] = []
    for product in products:
        row = dict(product)
        product_key = str(row.get("productKey") or "")
        assigned = sorted(inverse.get(product_key, []))
        key_materials = sorted(materials_by_key.get(product_key, set()))
        if len(key_materials) > 1 and coverage_status == COVERAGE_COMPLETE:
            # Múltiplos materiais sob o mesmo productKey — somar os atribuídos a este key.
            pass

        if not assigned:
            # Material exibido no produto pode ter sido atribuído a outro key.
            displayed = str(row.get("materialWegTratado") or "").strip()
            if displayed and assignment.get(displayed) and assignment[displayed] != product_key:
                row.update(_portal_fields_shared(displayed, reconciliations.get(displayed)))
            else:
                row.update(_portal_fields_empty(coverage_status))
            enriched.append(
                apply_managerial_classification(row, coverage_status=coverage_status)
            )
            continue

        recons = [reconciliations[m] for m in assigned if m in reconciliations]
        if not recons:
            row.update(_portal_fields_empty(coverage_status))
            enriched.append(
                apply_managerial_classification(row, coverage_status=coverage_status)
            )
            continue

        if coverage_status != COVERAGE_COMPLETE:
            observed = sum((r.observed_delta_un for r in recons), _ZERO)
            row.update(
                {
                    "observedDeltaUn": decimal_to_canonical_str(observed),
                    "postedQuantityUn": None,
                    "adjustedPlanningDeltaUn": None,
                    "compatibleReductionUn": None,
                    "invoiceMatchStatus": recons[0].invoice_match_status,
                    "portalInvoiceMaterials": [
                        _material_payload(r, attributed_to=product_key) for r in recons
                    ],
                    "portalInvoiceSources": _unique_sources(recons),
                }
            )
            enriched.append(
                apply_managerial_classification(row, coverage_status=coverage_status)
            )
            continue

        posted = sum((r.posted_nf_un for r in recons), _ZERO)
        observed = sum((r.observed_delta_un for r in recons), _ZERO)
        adjusted = sum(
            (r.adjusted_planning_delta_un or _ZERO for r in recons), _ZERO
        )
        compatible = sum(
            (r.compatible_reduction_un or _ZERO for r in recons), _ZERO
        )
        match_status = MATCH_OK
        if len(key_materials) > 1:
            match_status = MATCH_MULTI_MATERIAL
        elif len(assigned) == 1 and assigned[0] != str(row.get("materialWegTratado") or "").strip():
            match_status = MATCH_OK
        row.update(
            {
                "observedDeltaUn": decimal_to_canonical_str(observed),
                "postedQuantityUn": decimal_to_canonical_str(posted),
                "adjustedPlanningDeltaUn": decimal_to_canonical_str(adjusted),
                "compatibleReductionUn": decimal_to_canonical_str(compatible),
                "invoiceMatchStatus": match_status,
                "portalInvoiceMaterials": [
                    _material_payload(r, attributed_to=product_key) for r in recons
                ],
                "portalInvoiceSources": _unique_sources(recons),
            }
        )
        enriched.append(
            apply_managerial_classification(row, coverage_status=coverage_status)
        )

    # Materiais só com NF / necessidade e sem product row — anexar como itens aditivos.
    represented = {m for mats in inverse.values() for m in mats}
    for material, recon in reconciliations.items():
        if material in represented:
            continue
        if recon.posted_nf_un == _ZERO and recon.observed_delta_un == _ZERO:
            continue
        enriched.append(
            apply_managerial_classification(
            {
                "productKey": f"ref:{material}",
                "identityKind": "customer_reference",
                "identityConfirmed": False,
                "identityReliable": True,
                "verifiedProductCode": None,
                "materialWegTratado": material,
                "codigoReferenciaWeg": None,
                "previousQuantityUn": decimal_to_canonical_str(recon.previous_need_un),
                "currentQuantityUn": decimal_to_canonical_str(recon.current_need_un),
                "deltaQuantityUn": decimal_to_canonical_str(recon.observed_delta_un),
                "percentChange": None,
                "previousRemessaCount": 0,
                "currentRemessaCount": 0,
                "hasRemessaChanges": False,
                "situation": "unchanged",
                "remessas": [],
                "probableDateShifts": [],
                "observedDeltaUn": decimal_to_canonical_str(recon.observed_delta_un),
                "postedQuantityUn": (
                    decimal_to_canonical_str(recon.posted_nf_un)
                    if recon.adjusted_planning_delta_un is not None
                    else None
                ),
                "adjustedPlanningDeltaUn": (
                    decimal_to_canonical_str(recon.adjusted_planning_delta_un)
                    if recon.adjusted_planning_delta_un is not None
                    else None
                ),
                "compatibleReductionUn": (
                    decimal_to_canonical_str(recon.compatible_reduction_un)
                    if recon.compatible_reduction_un is not None
                    else None
                ),
                "invoiceMatchStatus": recon.invoice_match_status,
                "portalInvoiceMaterials": [
                    _material_payload(recon, attributed_to=f"ref:{material}")
                ],
                "portalInvoiceSources": list(recon.source_observation_ids),
                "portalInvoiceOrphan": True,
            },
                coverage_status=coverage_status,
            )
        )
    return enriched


def product_has_invoice_signal(row: Mapping[str, Any]) -> bool:
    """changesOnly no modo portal: inclui delta observado 0 com ajuste ≠ 0."""
    if row.get("situation") != "unchanged":
        return True
    adjusted = row.get("adjustedPlanningDeltaUn")
    if adjusted is None or adjusted == "":
        return False
    return _dec(adjusted) != _ZERO


def classify_managerial_status(
    row: Mapping[str, Any],
    *,
    coverage_status: str,
) -> dict[str, Any]:
    """Classificação gerencial explícita — não substitui campos brutos.

    ``invoiceMatchStatus=reconciled`` isolado NÃO prova Faturado.
    """
    match = str(row.get("invoiceMatchStatus") or "").strip()
    identity_reliable = bool(row.get("identityReliable", True))
    observed_raw = row.get("observedDeltaUn")
    if observed_raw is None or observed_raw == "":
        observed_raw = row.get("deltaQuantityUn")
    observed = _dec(observed_raw)
    posted_raw = row.get("postedQuantityUn")
    compatible_raw = row.get("compatibleReductionUn")
    adjusted_raw = row.get("adjustedPlanningDeltaUn")
    posted_known = posted_raw is not None and str(posted_raw).strip() != ""
    compatible_known = compatible_raw is not None and str(compatible_raw).strip() != ""
    adjusted_known = adjusted_raw is not None and str(adjusted_raw).strip() != ""
    posted = _dec(posted_raw) if posted_known else None
    compatible = _dec(compatible_raw) if compatible_known else None
    adjusted = _dec(adjusted_raw) if adjusted_known else None
    reduction = max(-observed, _ZERO)

    pending_reason = None
    if coverage_status != COVERAGE_COMPLETE:
        pending_reason = f"coverage:{coverage_status}"
    elif not identity_reliable:
        pending_reason = "identity_unreliable"
    elif match in MANAGERIAL_PENDING_MATCHES:
        pending_reason = f"match:{match}"
    elif row.get("portalInvoiceOrphan"):
        pending_reason = "orphan_invoice_signal"

    if pending_reason:
        return {
            "managerialStatus": MANAGERIAL_PENDING,
            "managerialReason": pending_reason,
            "managerialExplanation": (
                "Conciliação ainda não é confiável para concluir faturamento."
            ),
            "residualUnexplainedUn": (
                decimal_to_canonical_str(reduction - compatible)
                if compatible is not None and reduction > compatible
                else (decimal_to_canonical_str(reduction) if reduction > _ZERO else None)
            ),
            "remessaInvoicingContext": "product_only",
        }

    if (
        posted is not None
        and posted > _ZERO
        and observed < _ZERO
        and compatible is not None
        and adjusted is not None
        and compatible == reduction
        and adjusted == _ZERO
    ):
        return {
            "managerialStatus": MANAGERIAL_INVOICED,
            "managerialReason": "full_compatible_reduction",
            "managerialExplanation": (
                f"Redução de {decimal_to_canonical_str(reduction)} UN integralmente "
                "compatível com a NF MyWEG observada. Nenhuma redução residual identificada."
            ),
            "residualUnexplainedUn": decimal_to_canonical_str(_ZERO),
            "remessaInvoicingContext": "eligible",
        }

    if (
        posted is not None
        and posted > _ZERO
        and observed < _ZERO
        and compatible is not None
        and compatible > _ZERO
        and compatible < reduction
    ):
        residual = reduction - compatible
        return {
            "managerialStatus": MANAGERIAL_PARTIAL,
            "managerialReason": "partial_compatible_reduction",
            "managerialExplanation": (
                f"Parte da redução ({decimal_to_canonical_str(compatible)} UN) é compatível "
                f"com NF MyWEG; residual de {decimal_to_canonical_str(residual)} UN sem "
                "explicação fiscal."
            ),
            "residualUnexplainedUn": decimal_to_canonical_str(residual),
            "remessaInvoicingContext": "product_only",
        }

    if observed < _ZERO and (posted is None or posted == _ZERO or compatible == _ZERO):
        return {
            "managerialStatus": MANAGERIAL_INVESTIGATE,
            "managerialReason": "reduction_without_compatible_nf",
            "managerialExplanation": (
                "Redução observada sem NF MyWEG compatível na janela — exige análise."
            ),
            "residualUnexplainedUn": decimal_to_canonical_str(reduction),
            "remessaInvoicingContext": "product_only",
        }

    return {
        "managerialStatus": MANAGERIAL_OTHER,
        "managerialReason": "non_reduction_or_neutral",
        "managerialExplanation": None,
        "residualUnexplainedUn": None,
        "remessaInvoicingContext": "product_only",
    }


def annotate_remessas_managerial_context(row: dict[str, Any]) -> dict[str, Any]:
    """Marca remessas reduzidas como compatíveis com faturamento só no total do produto.

    Sem rateio de NF por data. Se houver aumentos simultâneos, mantém só o nível produto.
    """
    remessas = [dict(item) for item in (row.get("remessas") or [])]
    context = str(row.get("remessaInvoicingContext") or "")
    if (
        row.get("managerialStatus") != MANAGERIAL_INVOICED
        or context != "eligible"
        or not remessas
    ):
        for item in remessas:
            item.pop("managerialRemessaContext", None)
        row["remessas"] = remessas
        row["remessaInvoicingContext"] = "product_only"
        return row

    deltas = [_dec(item.get("deltaQuantityUn")) for item in remessas]
    if any(delta > _ZERO for delta in deltas):
        for item in remessas:
            item.pop("managerialRemessaContext", None)
        row["remessas"] = remessas
        row["remessaInvoicingContext"] = "product_only"
        return row

    observed = _dec(
        row.get("observedDeltaUn")
        if row.get("observedDeltaUn") not in (None, "")
        else row.get("deltaQuantityUn")
    )
    reduction_sum = sum((delta for delta in deltas if delta < _ZERO), _ZERO)
    if reduction_sum != observed:
        for item in remessas:
            item.pop("managerialRemessaContext", None)
        row["remessas"] = remessas
        row["remessaInvoicingContext"] = "product_only"
        return row

    for item, delta in zip(remessas, deltas):
        if delta < _ZERO:
            item["managerialRemessaContext"] = "compatible_with_invoicing"
        else:
            item.pop("managerialRemessaContext", None)
    row["remessas"] = remessas
    row["remessaInvoicingContext"] = "compatible_on_reduced_lines"
    return row


def apply_managerial_classification(
    row: Mapping[str, Any],
    *,
    coverage_status: str,
) -> dict[str, Any]:
    enriched = dict(row)
    classification = classify_managerial_status(
        enriched, coverage_status=coverage_status
    )
    enriched.update(classification)
    return annotate_remessas_managerial_context(enriched)


def build_reconciliations_for_materials(
    *,
    previous_by_material: Mapping[str, Decimal],
    current_by_material: Mapping[str, Decimal],
    posted_by_material: Mapping[str, Decimal],
    coverage_status: str,
    source_observation_ids: Sequence[str],
) -> dict[str, MaterialReconciliation]:
    materials = sorted(
        set(previous_by_material) | set(current_by_material) | set(posted_by_material)
    )
    out: dict[str, MaterialReconciliation] = {}
    for material in materials:
        out[material] = reconcile_material(
            material_weg=material,
            previous_need_un=previous_by_material.get(material, _ZERO),
            current_need_un=current_by_material.get(material, _ZERO),
            posted_nf_un=posted_by_material.get(material, _ZERO),
            coverage_status=coverage_status,
            source_observation_ids=source_observation_ids,
        )
    return out


def _prefer_product_key(
    material: str,
    candidates: Sequence[str],
    products_by_key: Mapping[str, Mapping[str, Any]],
) -> str:
    ref_key = f"ref:{material}"
    if ref_key in candidates:
        return ref_key
    verified = [
        key
        for key in candidates
        if str(products_by_key[key].get("identityKind") or "") == "verified_code"
    ]
    if verified:
        # Prefer current quantity present
        verified_sorted = sorted(
            verified,
            key=lambda key: (
                0 if _dec(products_by_key[key].get("currentQuantityUn")) > _ZERO else 1,
                key,
            ),
        )
        return verified_sorted[0]
    return sorted(candidates)[0]


def _portal_fields_empty(coverage_status: str) -> dict[str, Any]:
    status = {
        COVERAGE_COMPLETE: MATCH_NONE,
        COVERAGE_PARTIAL: MATCH_PARTIAL,
        COVERAGE_CONFLICT: MATCH_CONFLICT,
        COVERAGE_PENDING_INGESTION: MATCH_UNAVAILABLE,
        COVERAGE_UNAVAILABLE: MATCH_UNAVAILABLE,
    }.get(coverage_status, MATCH_UNAVAILABLE)
    return {
        "observedDeltaUn": None,
        "postedQuantityUn": None,
        "adjustedPlanningDeltaUn": None,
        "compatibleReductionUn": None,
        "invoiceMatchStatus": status,
        "portalInvoiceMaterials": [],
        "portalInvoiceSources": [],
    }


def _portal_fields_shared(
    material: str, recon: MaterialReconciliation | None
) -> dict[str, Any]:
    return {
        "observedDeltaUn": (
            decimal_to_canonical_str(recon.observed_delta_un) if recon else None
        ),
        "postedQuantityUn": None,
        "adjustedPlanningDeltaUn": None,
        "compatibleReductionUn": None,
        "invoiceMatchStatus": MATCH_SHARED,
        "portalInvoiceMaterials": [
            {
                "materialWeg": material,
                "attributedToProductKey": None,
                "note": "Quantidade fiscal atribuída a outra identidade do mesmo material.",
            }
        ],
        "portalInvoiceSources": list(recon.source_observation_ids) if recon else [],
    }


def _material_payload(
    recon: MaterialReconciliation, *, attributed_to: str
) -> dict[str, Any]:
    return {
        "materialWeg": recon.material_weg,
        "previousNeedUn": decimal_to_canonical_str(recon.previous_need_un),
        "currentNeedUn": decimal_to_canonical_str(recon.current_need_un),
        "observedDeltaUn": decimal_to_canonical_str(recon.observed_delta_un),
        "postedQuantityUn": decimal_to_canonical_str(recon.posted_nf_un),
        "adjustedPlanningDeltaUn": (
            decimal_to_canonical_str(recon.adjusted_planning_delta_un)
            if recon.adjusted_planning_delta_un is not None
            else None
        ),
        "compatibleReductionUn": (
            decimal_to_canonical_str(recon.compatible_reduction_un)
            if recon.compatible_reduction_un is not None
            else None
        ),
        "invoiceMatchStatus": recon.invoice_match_status,
        "attributedToProductKey": attributed_to,
        "sources": list(recon.source_observation_ids),
    }


def _unique_sources(recons: Sequence[MaterialReconciliation]) -> list[str]:
    seen: list[str] = []
    for recon in recons:
        for source in recon.source_observation_ids:
            if source not in seen:
                seen.append(source)
    return seen


def _pick_deterministic(group: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    def sort_key(row: Mapping[str, Any]) -> tuple:
        prepared = str(row.get("source_prepared_at") or "")
        collection_id = str(row.get("collection_id") or "")
        payload = str(row.get("payload_sha256") or "").lower()
        # Mais recente por preparação, depois ids estáveis.
        return (prepared, collection_id, payload)

    return sorted(group, key=sort_key, reverse=True)[0]


def _dec(value: Any) -> Decimal:
    if value is None or value == "":
        return _ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, type(None)):
        return date.fromisoformat(value.isoformat()[:10])
    text = str(value).strip()[:10]
    if not text:
        return None
    return date.fromisoformat(text)
