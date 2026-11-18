"""Causa canônica de cada regra do motor para a análise da CLARA.

Uma regra → uma causa. Sem prefixo genérico no fallback.
"""

from __future__ import annotations

RULE_CAUSES: dict[str, str] = {
    "coherence.cfop_vs_state": "lançamento",
    "coherence.icms_on_consumption_cfop": "tes",
    "coherence.icms_on_untaxed_cst": "tes",
    "coherence.ipi_on_consumption": "tes",
    "cte.booked_not_taker": "lançamento",
    "cte.cfop_mismatch": "lançamento",
    "cte.credit_mismatch": "tes",
    "cte.credit_without_right": "tes",
    "cte.cst_mismatch": "tes",
    "cte.icms_inconclusive": "tes",
    "cte.icms_not_credited": "tes",
    "cte.rate_or_base_mismatch": "lançamento",
    "cte.service_amount_mismatch": "lançamento",
    "fiscal_book.amount_mismatch": "lançamento",
    "fiscal_book.credit_against_tes": "tes",
    "fiscal_book.credit_missing": "tes",
    "fiscal_book.item_missing": "lançamento",
    "header.accessory_field": "lançamento",
    "header.icms_above_xml": "tes",
    "header.icms_base_mismatch": "lançamento",
    "header.icms_credit_short": "tes",
    "header.icms_not_credited": "tes",
    "header.ipi_not_booked": "tes",
    "header.issue_date_mismatch": "lançamento",
    "header.series_mismatch": "lançamento",
    "header.total_mismatch": "lançamento",
    "item.amount_mismatch": "lançamento",
    "item.cfop_differs_from_issued": "lançamento",
    "item.cfop_direction_swapped": "lançamento",
    "item.cfop_nature_mismatch": "lançamento",
    "item.cst_mismatch": "tes",
    "item.fuel_cfop": "lançamento",
    "item.highlighted_icms_not_credited": "tes",
    "item.icms_above_xml": "tes",
    "item.inbound_booked_as_purchase": "lançamento",
    "item.ipi_base_mismatch": "lançamento",
    "item.ipi_credit_mismatch": "tes",
    "item.ipi_without_tes_decision": "tes",
    "item.origin_mismatch": "cadastro",
    "item.rate_or_base_mismatch": "lançamento",
    "item.simples_credit_not_taken": "tes",
    "item.st_cfop_without_st": "lançamento",
    "item.st_mismatch": "tes",
    "item.st_on_non_st_cfop": "lançamento",
    "item.unusual_cfop_nature": "cadastro",
    "key.diverges_from_xml": "lançamento",
    "key.invalid": "lançamento",
    "key.missing": "lançamento",
    "key.number_mismatch": "lançamento",
    "key.series_mismatch": "lançamento",
    "key.species_mismatch": "lançamento",
    "key.supplier_mismatch": "fornecedor",
    "simples.csosn_without_rate": "fornecedor",
    "simples.near_sublimite": "fornecedor",
    "simples.presumed_above_sublimite": "fornecedor",
    "simples.presumed_rate_mismatch": "tes",
    "simples.presumed_without_right": "fornecedor",
    "simples.presumed_wrong_tes": "cadastro",
    "simples.rate_above_cap": "fornecedor",
}

KNOWN_CAUSES = ("cadastro", "lançamento", "fornecedor", "tes")


def cause_for(rule_id: str) -> str:
    key = str(rule_id or "")
    if key in RULE_CAUSES:
        return RULE_CAUSES[key]
    if key.startswith("unmatched."):
        return "lançamento"
    raise KeyError(f"regra sem causa canônica: {rule_id}")


# FA-4 — identidade da causa para agrupar hits da mesma divergência numa
# ocorrência só. Regras não listadas viram causa 1:1 pelo próprio rule_id.
RULE_CAUSE_IDS: dict[str, str] = {
    # Cabeçalho e item da mesma divergência de ICMS = uma causa (NF-B).
    "header.icms_above_xml": "icms_amount",
    "item.icms_above_xml": "icms_amount",
    "header.icms_credit_short": "icms_amount",
    "header.icms_base_mismatch": "icms_base",
    # IPI: destaque no cabeçalho e crédito no item são a mesma divergência.
    "header.ipi_not_booked": "ipi_amount",
    "item.ipi_credit_mismatch": "ipi_amount",
}


def cause_id_for(rule_id: str) -> str:
    """`cause_id` canônico do hit (FA-4). Fallback 1:1 pelo rule_id."""
    key = str(rule_id or "")
    return RULE_CAUSE_IDS.get(key, key)
