"""Classificação de correspondência SB1 por igualdade exata (sem LIKE/prefixo).

Estados:
- confirmed: produto elegível alinhado (par informado ou desempate por política)
- not_found: nenhum produto
- ambiguous: dois ou mais produtos sem desempate válido
- divergent: código informado não corresponde à referência
- blocked: candidato informado/único com B1_MSBLQL = '1'
- pending: sem código e sem referência (nada a consultar)

Com disambiguation_policy=prefer_production_over_sample:
1) código 9 de origem validado pelo par B1_COD+B1_REFEREN tem prioridade absoluta;
2) senão, entre elegíveis da mesma B1_REFEREN, escolhe o maior B1_COD numérico
   priorizando prefixo 9 sobre 8.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

MATCH_CONFIRMED = "confirmed"
MATCH_NOT_FOUND = "not_found"
MATCH_AMBIGUOUS = "ambiguous"
MATCH_DIVERGENT = "divergent"
MATCH_BLOCKED = "blocked"
MATCH_PENDING = "pending"

MATCHED_BY_CODE_AND_REFERENCE = "code_and_reference"
MATCHED_BY_REFERENCE_ONLY = "reference_only"
MATCHED_BY_CODE_ONLY = "code_only"
MATCHED_BY_REFERENCE_PREFER_PRODUCTION = "reference_prefer_production"

# Política opcional (MyWEG / PCP): 9=produção, 8=amostra. Default None = sem preferência.
DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE = "prefer_production_over_sample"
_ALLOWED_DISAMBIGUATION = frozenset({DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE})

BLOCKED_FLAG = "1"
_PRODUCTION_PREFIX = "9"
_SAMPLE_PREFIX = "8"


def normalize_sb1_token(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def is_blocked_flag(flag: str | None) -> bool:
    return str(flag or "").strip() == BLOCKED_FLAG


def _product_view(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "product_code": normalize_sb1_token(row.get("product_code")) or "",
        "description": str(row.get("description") or "").strip(),
        "product_type": str(row.get("product_type") or "").strip(),
        "unit": str(row.get("unit") or "").strip(),
        "group_code": str(row.get("group_code") or "").strip(),
        "customer_reference": normalize_sb1_token(row.get("customer_reference")),
        "blocked": is_blocked_flag(row.get("blocked_flag")),
        "blocked_flag": str(row.get("blocked_flag") or "").strip(),
    }


def classify_sb1_identity_pair(
    *,
    product_code: str | None,
    customer_reference: str | None,
    by_code: Mapping[str, Any] | None,
    by_reference: Sequence[Mapping[str, Any]],
    disambiguation_policy: str | None = None,
) -> dict[str, Any]:
    """Classifica um par (código, referência) contra hits exatos do cadastro."""
    code = normalize_sb1_token(product_code)
    reference = normalize_sb1_token(customer_reference)
    code_product = _product_view(by_code) if by_code else None
    ref_products = [_product_view(row) for row in by_reference if row]
    policy = _normalize_policy(disambiguation_policy)

    base = {
        "product_code": code,
        "customer_reference": reference,
        "matched_by": None,
        "verified_product_code": None,
        "verified_description": None,
        "candidates": [],
        "reason": None,
    }

    if code is None and reference is None:
        return {
            **base,
            "match_status": MATCH_PENDING,
            "reason": "missing_code_and_reference",
        }

    if code is not None:
        if code_product is None:
            if reference is None:
                return {
                    **base,
                    "match_status": MATCH_NOT_FOUND,
                    "reason": "product_code_not_found",
                }
            if not ref_products:
                return {
                    **base,
                    "match_status": MATCH_NOT_FOUND,
                    "reason": "product_code_and_reference_not_found",
                }
            if len(ref_products) > 1:
                result = {
                    **base,
                    "match_status": MATCH_AMBIGUOUS,
                    "candidates": ref_products,
                    "reason": "product_code_not_found_reference_ambiguous",
                }
                # Código informado inexistente: nunca substituir por preferência 9/8.
                return result
            # Código informado não existe, mas a referência aponta para um produto —
            # não substituir silenciosamente (RQ-04).
            only = ref_products[0]
            return {
                **base,
                "match_status": MATCH_DIVERGENT,
                "candidates": ref_products,
                "verified_product_code": only["product_code"] or None,
                "verified_description": only["description"] or None,
                "reason": "informed_code_missing_reference_maps_elsewhere",
            }

        code_ref = code_product["customer_reference"]
        if reference is not None and code_ref != reference:
            return {
                **base,
                "match_status": MATCH_DIVERGENT,
                "candidates": [code_product, *ref_products],
                "verified_product_code": code_product["product_code"] or None,
                "verified_description": code_product["description"] or None,
                "reason": "informed_code_reference_mismatch",
            }

        if code_product["blocked"]:
            result = {
                **base,
                "match_status": MATCH_BLOCKED,
                "verified_product_code": code_product["product_code"] or None,
                "verified_description": code_product["description"] or None,
                "matched_by": (
                    MATCHED_BY_CODE_AND_REFERENCE
                    if reference is not None
                    else MATCHED_BY_CODE_ONLY
                ),
                "candidates": [code_product],
                "reason": "product_blocked",
            }
            return _apply_production_preference(
                result, ref_products=ref_products, policy=policy
            )

        result = {
            **base,
            "match_status": MATCH_CONFIRMED,
            "verified_product_code": code_product["product_code"] or None,
            "verified_description": code_product["description"] or None,
            "matched_by": (
                MATCHED_BY_CODE_AND_REFERENCE
                if reference is not None
                else MATCHED_BY_CODE_ONLY
            ),
            "candidates": [code_product],
            "reason": None,
        }
        return _apply_production_preference(
            result, ref_products=ref_products, policy=policy
        )

    # Sem código informado — só referência (RQ-02 / RQ-03).
    if not ref_products:
        return {
            **base,
            "match_status": MATCH_NOT_FOUND,
            "reason": "customer_reference_not_found",
        }
    if len(ref_products) > 1:
        result = {
            **base,
            "match_status": MATCH_AMBIGUOUS,
            "candidates": ref_products,
            "reason": "customer_reference_ambiguous",
        }
        return _apply_production_preference(
            result, ref_products=ref_products, policy=policy
        )

    only = ref_products[0]
    if only["blocked"]:
        result = {
            **base,
            "match_status": MATCH_BLOCKED,
            "verified_product_code": only["product_code"] or None,
            "verified_description": only["description"] or None,
            "matched_by": MATCHED_BY_REFERENCE_ONLY,
            "candidates": [only],
            "reason": "product_blocked",
        }
        return _apply_production_preference(
            result, ref_products=ref_products, policy=policy
        )

    result = {
        **base,
        "match_status": MATCH_CONFIRMED,
        "verified_product_code": only["product_code"] or None,
        "verified_description": only["description"] or None,
        "matched_by": MATCHED_BY_REFERENCE_ONLY,
        "candidates": [only],
        "reason": None,
    }
    return _apply_production_preference(
        result, ref_products=ref_products, policy=policy
    )


def _normalize_policy(value: str | None) -> str | None:
    text = str(value or "").strip() or None
    if text is None:
        return None
    if text not in _ALLOWED_DISAMBIGUATION:
        raise ValueError(
            "disambiguation_policy inválida. "
            f"Use '{DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE}' ou omita."
        )
    return text


def _is_production_code(code: str | None) -> bool:
    return bool(code) and str(code).startswith(_PRODUCTION_PREFIX)


def _is_sample_code(code: str | None) -> bool:
    return bool(code) and str(code).startswith(_SAMPLE_PREFIX)


def _numeric_code_value(code: str | None) -> int | None:
    """Valor numérico para desempate; None se não for dígitos puros."""
    text = normalize_sb1_token(code)
    if text is None or not text.isdigit():
        return None
    return int(text)


def _dedupe_by_product_code(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        code = normalize_sb1_token(row.get("product_code")) or ""
        if not code or code in seen:
            continue
        seen.add(code)
        unique.append(dict(row))
    return unique


def _select_highest_numeric_code(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Maior B1_COD numérico; None se não houver candidato numérico inequívoco."""
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        value = _numeric_code_value(row.get("product_code"))
        if value is None:
            continue
        scored.append((value, dict(row)))
    if not scored:
        return None
    max_value = max(value for value, _ in scored)
    winners = [row for value, row in scored if value == max_value]
    winner_codes = {
        normalize_sb1_token(row.get("product_code")) for row in winners
    } - {None}
    if len(winner_codes) != 1:
        return None
    return winners[0]


def _apply_production_preference(
    result: dict[str, Any],
    *,
    ref_products: Sequence[Mapping[str, Any]],
    policy: str | None,
) -> dict[str, Any]:
    """Preferência PCP 9/8 — origem 9 válida vence; senão maior código numérico."""
    if policy != DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE:
        return result

    status = str(result.get("match_status") or "")
    if status in {MATCH_DIVERGENT, MATCH_PENDING, MATCH_NOT_FOUND}:
        return result

    informed = normalize_sb1_token(result.get("product_code"))
    verified = normalize_sb1_token(result.get("verified_product_code"))
    reference = normalize_sb1_token(result.get("customer_reference"))

    # Código 9 informado e bloqueado: manter blocked (não trocar por outro elegível).
    if (
        status == MATCH_BLOCKED
        and _is_production_code(informed)
        and informed == verified
    ):
        return result

    # Universo da referência WEG; inclui candidatos quando a lista por referência veio vazia.
    universe = [dict(row) for row in ref_products]
    if not universe and result.get("candidates"):
        universe = [dict(row) for row in result["candidates"]]
    if reference is not None:
        universe = [
            row
            for row in universe
            if normalize_sb1_token(row.get("customer_reference")) == reference
        ]
    universe = _dedupe_by_product_code(universe)
    if not universe:
        return result

    # Prioridade absoluta: origem 9 confirmada pelo par B1_COD + B1_REFEREN.
    # Contrapeças com código maior NÃO sobrescrevem essa confirmação.
    if (
        status == MATCH_CONFIRMED
        and _is_production_code(informed)
        and informed == verified
        and result.get("matched_by") == MATCHED_BY_CODE_AND_REFERENCE
    ):
        return {
            **result,
            "match_status": MATCH_CONFIRMED,
            "verified_product_code": informed,
            "verified_description": result.get("verified_description"),
            "matched_by": MATCHED_BY_CODE_AND_REFERENCE,
            "candidates": list(universe),
            "reason": None,
        }

    eligible = [row for row in universe if not row.get("blocked")]
    productions = [
        row for row in eligible if _is_production_code(row.get("product_code"))
    ]
    samples = [row for row in eligible if _is_sample_code(row.get("product_code"))]

    if productions:
        chosen = _select_highest_numeric_code(productions)
        if chosen is None:
            return {
                **result,
                "match_status": MATCH_AMBIGUOUS,
                "verified_product_code": None,
                "verified_description": None,
                "matched_by": None,
                "candidates": list(universe),
                "reason": "multiple_production_codes",
            }
        selected = normalize_sb1_token(chosen.get("product_code"))
        exact = bool(informed and selected and informed == selected)
        return {
            **result,
            "match_status": MATCH_CONFIRMED,
            "verified_product_code": selected,
            "verified_description": chosen.get("description") or None,
            "matched_by": (
                MATCHED_BY_CODE_AND_REFERENCE
                if exact
                else MATCHED_BY_REFERENCE_PREFER_PRODUCTION
            ),
            "candidates": list(universe),
            "reason": None if exact else "prefer_highest_production_code",
        }

    # Sem produção elegível: maior amostra 8 numérica (provisória).
    if samples:
        chosen = _select_highest_numeric_code(samples)
        if chosen is None:
            return result
        selected = normalize_sb1_token(chosen.get("product_code"))
        exact = bool(
            informed
            and selected
            and informed == selected
            and result.get("customer_reference")
        )
        reason = (
            "provisional_sample_code_no_production"
            if len(samples) == 1
            else "provisional_highest_sample_code_no_production"
        )
        return {
            **result,
            "match_status": MATCH_CONFIRMED,
            "verified_product_code": selected,
            "verified_description": chosen.get("description") or None,
            "matched_by": (
                MATCHED_BY_CODE_AND_REFERENCE if exact else MATCHED_BY_REFERENCE_ONLY
            ),
            "candidates": list(universe),
            "reason": reason,
        }

    return result
