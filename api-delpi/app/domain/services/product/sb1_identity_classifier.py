"""Classificação de correspondência SB1 por igualdade exata (sem LIKE/prefixo).

Estados:
- confirmed: único produto elegível alinhado ao par informado
- not_found: nenhum produto
- ambiguous: dois ou mais produtos para a referência
- divergent: código informado não corresponde à referência
- blocked: único candidato com B1_MSBLQL = '1'
- pending: sem código e sem referência (nada a consultar)
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

BLOCKED_FLAG = "1"


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
) -> dict[str, Any]:
    """Classifica um par (código, referência) contra hits exatos do cadastro."""
    code = normalize_sb1_token(product_code)
    reference = normalize_sb1_token(customer_reference)
    code_product = _product_view(by_code) if by_code else None
    ref_products = [_product_view(row) for row in by_reference if row]

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
                return {
                    **base,
                    "match_status": MATCH_AMBIGUOUS,
                    "candidates": ref_products,
                    "reason": "product_code_not_found_reference_ambiguous",
                }
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
            return {
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

        return {
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

    # Sem código informado — só referência (RQ-02 / RQ-03).
    if not ref_products:
        return {
            **base,
            "match_status": MATCH_NOT_FOUND,
            "reason": "customer_reference_not_found",
        }
    if len(ref_products) > 1:
        return {
            **base,
            "match_status": MATCH_AMBIGUOUS,
            "candidates": ref_products,
            "reason": "customer_reference_ambiguous",
        }

    only = ref_products[0]
    if only["blocked"]:
        return {
            **base,
            "match_status": MATCH_BLOCKED,
            "verified_product_code": only["product_code"] or None,
            "verified_description": only["description"] or None,
            "matched_by": MATCHED_BY_REFERENCE_ONLY,
            "candidates": [only],
            "reason": "product_blocked",
        }

    return {
        **base,
        "match_status": MATCH_CONFIRMED,
        "verified_product_code": only["product_code"] or None,
        "verified_description": only["description"] or None,
        "matched_by": MATCHED_BY_REFERENCE_ONLY,
        "candidates": [only],
        "reason": None,
    }
