"""Comparação pura entre snapshots MyWEG — sem I/O, sem Protheus.

Variação observada ≠ abatimento reconhecido pela WEG.
FIFO de faturamento é cenário hipotético separado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

ZERO = Decimal("0")
HORIZON_DAYS = 14


@dataclass(frozen=True)
class NeedKey:
    """Identidade segura produto+remessa entre coletas (não usa line_fingerprint)."""

    product_key: str
    remessa: date
    identity_kind: str  # verified_code | customer_reference | unresolved


@dataclass(frozen=True)
class AggregatedNeed:
    key: NeedKey
    material_weg_tratado: str | None
    codigo_referencia_weg: str | None
    verified_product_code: str | None
    quantity_un: Decimal
    quantity_mi: Decimal
    line_count: int


def _dec(value: Any) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, type(None)):
        # datetime is subclass of date
        text = value.isoformat()[:10]
        return date.fromisoformat(text)
    text = str(value).strip()[:10]
    if not text:
        return None
    return date.fromisoformat(text)


def resolve_product_identity(row: Mapping[str, Any]) -> tuple[str, str, str | None]:
    """Retorna (product_key, identity_kind, verified_code)."""
    sb1 = row.get("sb1_resolution") or {}
    status = str(sb1.get("status") or "").strip().lower()
    verified = (sb1.get("protheus_product_code") or sb1.get("verified_product_code") or "")
    verified = str(verified).strip() or None
    if status == "confirmed" and verified:
        return f"code:{verified}", "verified_code", verified
    material = str(row.get("material_weg_tratado") or "").strip()
    if material:
        return f"ref:{material}", "customer_reference", verified
    informed = str(row.get("codigo_referencia_weg") or "").strip()
    if informed:
        return f"informed:{informed}", "unresolved", verified
    return "unresolved:empty", "unresolved", verified


def aggregate_needs(rows: Sequence[Mapping[str, Any]]) -> dict[NeedKey, AggregatedNeed]:
    buckets: dict[NeedKey, AggregatedNeed] = {}
    for row in rows:
        remessa = _parse_date(row.get("data_remessa"))
        if remessa is None:
            continue
        product_key, kind, verified = resolve_product_identity(row)
        key = NeedKey(product_key=product_key, remessa=remessa, identity_kind=kind)
        qty_un = _dec(row.get("quantidade_original_un"))
        qty_mi = _dec(row.get("quantidade_mi"))
        existing = buckets.get(key)
        if existing is None:
            buckets[key] = AggregatedNeed(
                key=key,
                material_weg_tratado=str(row.get("material_weg_tratado") or "").strip() or None,
                codigo_referencia_weg=str(row.get("codigo_referencia_weg") or "").strip() or None,
                verified_product_code=verified,
                quantity_un=qty_un,
                quantity_mi=qty_mi,
                line_count=1,
            )
        else:
            buckets[key] = AggregatedNeed(
                key=key,
                material_weg_tratado=existing.material_weg_tratado
                or (str(row.get("material_weg_tratado") or "").strip() or None),
                codigo_referencia_weg=existing.codigo_referencia_weg
                or (str(row.get("codigo_referencia_weg") or "").strip() or None),
                verified_product_code=existing.verified_product_code or verified,
                quantity_un=existing.quantity_un + qty_un,
                quantity_mi=existing.quantity_mi + qty_mi,
                line_count=existing.line_count + 1,
            )
    return buckets


def compare_aggregated(
    previous: Mapping[NeedKey, AggregatedNeed],
    current: Mapping[NeedKey, AggregatedNeed],
    *,
    reference_date: date,
) -> dict[str, Any]:
    """Diferenças observadas entre duas agregações (sem faturamento)."""
    horizon_end = reference_date + timedelta(days=HORIZON_DAYS)
    all_keys = sorted(
        set(previous) | set(current),
        key=lambda k: (k.product_key, k.remessa.isoformat()),
    )
    changes: list[dict[str, Any]] = []
    summary = {
        "unchanged": 0,
        "increased": 0,
        "decreased": 0,
        "appeared": 0,
        "disappeared": 0,
        "horizon_14d_changes": 0,
        "uncertain_identity_keys": 0,
    }
    for key in all_keys:
        prev = previous.get(key)
        curr = current.get(key)
        prev_un = prev.quantity_un if prev else ZERO
        curr_un = curr.quantity_un if curr else ZERO
        delta = curr_un - prev_un
        if delta == ZERO and prev is not None and curr is not None:
            movement = "unchanged"
            summary["unchanged"] += 1
        elif prev is None:
            movement = "appeared"
            summary["appeared"] += 1
        elif curr is None:
            movement = "disappeared"
            summary["disappeared"] += 1
        elif delta > ZERO:
            movement = "increased"
            summary["increased"] += 1
        else:
            movement = "decreased"
            summary["decreased"] += 1

        in_horizon = reference_date <= key.remessa <= horizon_end
        if movement != "unchanged" and in_horizon:
            summary["horizon_14d_changes"] += 1
        if key.identity_kind == "unresolved":
            summary["uncertain_identity_keys"] += 1

        sample = curr or prev
        assert sample is not None
        changes.append(
            {
                "productKey": key.product_key,
                "identityKind": key.identity_kind,
                "remessa": key.remessa.isoformat(),
                "inHorizon14d": in_horizon,
                "movement": movement,
                "previousQuantityUn": str(prev_un),
                "currentQuantityUn": str(curr_un),
                "deltaQuantityUn": str(delta),
                "previousQuantityMi": str(prev.quantity_mi if prev else ZERO),
                "currentQuantityMi": str(curr.quantity_mi if curr else ZERO),
                "materialWegTratado": sample.material_weg_tratado,
                "codigoReferenciaWeg": sample.codigo_referencia_weg,
                "verifiedProductCode": sample.verified_product_code,
                "previousLineCount": prev.line_count if prev else 0,
                "currentLineCount": curr.line_count if curr else 0,
            }
        )

    # Movimentos prováveis entre datas do mesmo produto (sem pairing individual).
    probable = _probable_date_shifts(previous, current)

    return {
        "summary": summary,
        "changes": changes,
        "probableDateShifts": probable,
        "horizonDays": HORIZON_DAYS,
        "referenceDate": reference_date.isoformat(),
    }


def _probable_date_shifts(
    previous: Mapping[NeedKey, AggregatedNeed],
    current: Mapping[NeedKey, AggregatedNeed],
) -> list[dict[str, Any]]:
    products = {k.product_key for k in set(previous) | set(current)}
    out: list[dict[str, Any]] = []
    for product in sorted(products):
        prev_by_date = {
            k.remessa: v.quantity_un
            for k, v in previous.items()
            if k.product_key == product
        }
        curr_by_date = {
            k.remessa: v.quantity_un
            for k, v in current.items()
            if k.product_key == product
        }
        dates = sorted(set(prev_by_date) | set(curr_by_date))
        decreases: list[tuple[date, Decimal]] = []
        increases: list[tuple[date, Decimal]] = []
        for d in dates:
            delta = curr_by_date.get(d, ZERO) - prev_by_date.get(d, ZERO)
            if delta < ZERO:
                decreases.append((d, -delta))
            elif delta > ZERO:
                increases.append((d, delta))
        # Pareamento grosseiro: não afirma identidade de linha.
        di, ii = 0, 0
        while di < len(decreases) and ii < len(increases):
            d_date, d_qty = decreases[di]
            i_date, i_qty = increases[ii]
            moved = min(d_qty, i_qty)
            if moved > ZERO:
                kind = "possible_advancement" if i_date < d_date else (
                    "possible_postponement" if i_date > d_date else "same_date_redistribution"
                )
                out.append(
                    {
                        "productKey": product,
                        "fromRemessa": d_date.isoformat(),
                        "toRemessa": i_date.isoformat(),
                        "quantityUn": str(moved),
                        "kind": kind,
                        "confidence": "probable_not_proven",
                    }
                )
            d_qty -= moved
            i_qty -= moved
            decreases[di] = (d_date, d_qty)
            increases[ii] = (i_date, i_qty)
            if d_qty == ZERO:
                di += 1
            if i_qty == ZERO:
                ii += 1
    return out


def simulate_fifo_abatement(
    previous_needs: Mapping[NeedKey, AggregatedNeed],
    *,
    product_key: str,
    candidate_quantity_un: Decimal,
) -> dict[str, Any]:
    """Simulação hipotética FIFO por remessa ascendente — não prova reconhecimento WEG.

    Excedente além da necessidade anterior não gera saldo negativo.
    """
    if candidate_quantity_un < ZERO:
        raise ValueError("candidate_quantity_un não pode ser negativo.")

    rows = sorted(
        (v for k, v in previous_needs.items() if k.product_key == product_key),
        key=lambda item: item.key.remessa,
    )
    remaining = candidate_quantity_un
    result_rows: list[dict[str, Any]] = []
    for need in rows:
        before = need.quantity_un
        abated = min(before, remaining)
        after = before - abated
        remaining -= abated
        result_rows.append(
            {
                "remessa": need.key.remessa.isoformat(),
                "previousQuantityUn": str(before),
                "hypotheticalQuantityUn": str(after),
                "abatedQuantityUn": str(abated),
            }
        )
    return {
        "productKey": product_key,
        "candidateQuantityUn": str(candidate_quantity_un),
        "appliedQuantityUn": str(candidate_quantity_un - remaining),
        "unusedCandidateQuantityUn": str(remaining),
        "rows": result_rows,
        "disclaimer": (
            "Cenário hipotético se a WEG tivesse reconhecido integralmente "
            "o faturamento candidato. Não comprova abatimento."
        ),
    }


def build_product_fifo_scenarios(
    previous: Mapping[NeedKey, AggregatedNeed],
    current: Mapping[NeedKey, AggregatedNeed],
    billing_by_product: Mapping[str, Decimal],
) -> list[dict[str, Any]]:
    """FIFO por produto + residual vs necessidade atual (ainda hipotético)."""
    scenarios: list[dict[str, Any]] = []
    products = sorted(
        {k.product_key for k in previous}
        | {k.product_key for k in current}
        | set(billing_by_product)
    )
    for product in products:
        candidate = _dec(billing_by_product.get(product, ZERO))
        if candidate == ZERO and not any(k.product_key == product for k in previous):
            continue
        fifo = simulate_fifo_abatement(
            previous, product_key=product, candidate_quantity_un=candidate
        )
        # Residual: atual observado vs hipotético pós-FIFO (por remessa).
        hyp_by_date = {
            row["remessa"]: _dec(row["hypotheticalQuantityUn"]) for row in fifo["rows"]
        }
        residuals: list[dict[str, Any]] = []
        dates = sorted(
            {
                *hyp_by_date.keys(),
                *(
                    k.remessa.isoformat()
                    for k in current
                    if k.product_key == product
                ),
            }
        )
        for remessa in dates:
            hyp = hyp_by_date.get(remessa, ZERO)
            curr_keys = [
                v
                for k, v in current.items()
                if k.product_key == product and k.remessa.isoformat() == remessa
            ]
            curr_qty = sum((v.quantity_un for v in curr_keys), ZERO)
            residuals.append(
                {
                    "remessa": remessa,
                    "hypotheticalQuantityUn": str(hyp),
                    "currentQuantityUn": str(curr_qty),
                    "residualQuantityUn": str(curr_qty - hyp),
                }
            )
        scenarios.append(
            {
                **fifo,
                "residualsVsCurrent": residuals,
            }
        )
    return scenarios
