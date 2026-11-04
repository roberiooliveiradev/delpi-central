"""Prova de semântica dos campos MyWEG × SB1 antes de persistir vínculos.

Hipótese a validar (não presumir):
- material_weg_tratado → SB1.B1_REFEREN
- codigo_referencia_weg → SB1.B1_COD (rótulo E1 enganoso)

A prova usa amostragem dos pares onde ambos os campos existem e o lookup
classificou confirmed com matched_by=code_and_reference, ou divergent com
informed_code_reference_mismatch (evidência contrária).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

MIN_PAIRS_FOR_PROOF = 20
MIN_CONFIRM_RATIO = 0.80


def evaluate_field_semantics(
    pair_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Avalia se a hipótese de campos está comprovada pelos resultados do lookup."""
    both_present = [
        row
        for row in pair_results
        if row.get("product_code") and row.get("customer_reference")
    ]
    confirmed_aligned = [
        row
        for row in both_present
        if row.get("match_status") == "confirmed"
        and row.get("matched_by") == "code_and_reference"
    ]
    divergent_mismatch = [
        row
        for row in both_present
        if row.get("match_status") == "divergent"
        and row.get("reason") == "informed_code_reference_mismatch"
    ]
    code_found = [
        row
        for row in both_present
        if row.get("match_status") in {"confirmed", "blocked", "divergent"}
        and row.get("verified_product_code")
    ]

    sample_size = len(both_present)
    confirm_count = len(confirmed_aligned)
    diverge_count = len(divergent_mismatch)
    code_hit_count = len(code_found)
    confirm_ratio = (confirm_count / sample_size) if sample_size else 0.0
    code_hit_ratio = (code_hit_count / sample_size) if sample_size else 0.0

    proven = (
        sample_size >= MIN_PAIRS_FOR_PROOF
        and confirm_ratio >= MIN_CONFIRM_RATIO
        and diverge_count / sample_size <= (1.0 - MIN_CONFIRM_RATIO)
    )

    notes = (
        f"pairs_both_fields={sample_size}; "
        f"confirmed_code_and_reference={confirm_count} ({confirm_ratio:.1%}); "
        f"divergent_mismatch={diverge_count}; "
        f"code_hits={code_hit_count} ({code_hit_ratio:.1%}); "
        f"threshold=min_pairs:{MIN_PAIRS_FOR_PROOF}, min_confirm_ratio:{MIN_CONFIRM_RATIO}"
    )

    return {
        "proven": proven,
        "sample_size": sample_size,
        "confirm_count": confirm_count,
        "diverge_count": diverge_count,
        "code_hit_count": code_hit_count,
        "confirm_ratio": round(confirm_ratio, 4),
        "code_hit_ratio": round(code_hit_ratio, 4),
        "hypothesis": {
            "material_weg_tratado": "SB1.B1_REFEREN",
            "codigo_referencia_weg": "SB1.B1_COD",
        },
        "notes": notes,
        "architecture_decision_required": not proven,
    }
