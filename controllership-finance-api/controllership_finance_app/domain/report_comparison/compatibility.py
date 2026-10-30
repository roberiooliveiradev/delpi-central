"""GATE C — semantic compatibility matrix (doc 126 §7 + decision D-05).

Three functional results approved by the PO:

- ``COMPARABLE`` — a numeric delta (and percentage, when the baseline
  is non-zero) is meaningful;
- ``RELATED_REQUIRES_EXPLANATION`` — the measures are related but not
  equivalent: totals may be shown side by side and the difference may
  be *displayed* with the mandatory explanation, but it is never a
  proven financial divergence;
- ``NOT_COMPARABLE`` — no common measure; only a qualitative analysis
  may be offered.

Anything not explicitly classified falls back to
``INSUFFICIENT_EVIDENCE`` — never inferred from similar column names.
"""

from __future__ import annotations

from dataclasses import dataclass, field


COMPARABLE = "COMPARABLE"
RELATED_REQUIRES_EXPLANATION = "RELATED_REQUIRES_EXPLANATION"
NOT_COMPARABLE = "NOT_COMPARABLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class CompatibilityVerdict:
    classification: str
    reason: str
    explanation: str
    evidence_refs: tuple[str, ...] = ()
    numeric_delta_allowed: bool = False
    delta_semantics: str | None = None
    conditions: tuple[str, ...] = ()


def _verdict(
    classification: str,
    reason: str,
    explanation: str,
    *,
    evidence: tuple[str, ...] = (),
    delta: bool = False,
    delta_semantics: str | None = None,
    conditions: tuple[str, ...] = (),
) -> CompatibilityVerdict:
    return CompatibilityVerdict(
        classification=classification,
        reason=reason,
        explanation=explanation,
        evidence_refs=evidence,
        numeric_delta_allowed=delta,
        delta_semantics=delta_semantics,
        conditions=conditions,
    )


# ------------------------------------------------------------------
# cross-report pairs — keyed by frozenset({rid_a, rid_b})
# ------------------------------------------------------------------

_PAIR_MATRIX: dict[frozenset[str], CompatibilityVerdict] = {
    frozenset({"R05", "R06"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "raw_flow_vs_valued_kardex",
        (
            "R05 mede o fluxo valorizado do mês por tipo de produto "
            "(equação de saldo); R06 mede o kardex com custo as-of "
            "TTAT. Quantidades sao comparáveis por produto/tipo; "
            "valores divergem pela convenção de custo — a diferença "
            "não é divergência financeira comprovada."
        ),
        evidence=("doc-126#7", "doc-85#BR-R05-006"),
        delta=True,
        delta_semantics="related_not_equivalent",
    ),
    frozenset({"R06", "CPV"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "stock_output_vs_managerial_cpv",
        (
            "Saída de estoque (R06, F4_ESTOQUE='S' + valorização "
            "TTAT) NÃO é o CPV: CPV é SUM(D2_CUSTO1) sobre CFOP de "
            "venda com custo corrente ('live'). Escopo, sinal, eixo "
            "e base de custo distintos — explicável por item-irmão "
            "(TES 510 custo>0 + TES 594 custo 0). A diferença não é "
            "divergência financeira comprovada."
        ),
        evidence=("doc-126#7", "doc-85#10", "doc-80#45"),
        delta=True,
        delta_semantics="related_not_equivalent",
    ),
    frozenset({"R06", "R07"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "invent_subset_vs_full_kardex",
        (
            "R07 é o subconjunto D3_DOC='INVENT' dos movimentos do "
            "motor R06 — comparável apenas com filtro explícito de "
            "documento, nunca como total do kardex."
        ),
        evidence=("doc-126#7", "doc-122#R07"),
        delta=True,
        delta_semantics="subset_relation",
    ),
    frozenset({"R03", "R05"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "static_snapshot_vs_flow",
        (
            "R03 é a posição estática SB9 no corte; R05 é o fluxo "
            "valorizado do período. Relacionados pela equação de "
            "saldo, mas dimensão estática × fluxo — nenhum delta "
            "direto certifica reconciliação."
        ),
        evidence=("doc-126#7",),
    ),
    frozenset({"R03", "R08"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "disjoint_stock_universes",
        (
            "R03 (EM ESTOQUE, exclui armazém de processo) e R08 "
            "(material em processo, loc99 + alocado) são partições "
            "disjuntas do universo SB9 por MV_LOCPROC — comparáveis "
            "só como componentes da composição de saldo."
        ),
        evidence=("doc-126#7", "doc-84#5"),
    ),
    frozenset({"R10", "R11"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "sd1_expenses_vs_sd2_roster",
        (
            "R10 = itens SD1 de despesa no eixo D1_DTDIGIT; R11 = "
            "itens SD2 do roster investigativo no eixo D2_EMISSAO. "
            "Mesmo grão NF/item mas eixos de data e tabelas "
            "distintos — a relação documental exige chave completa "
            "(filial+documento+série); nunca cruzar só por número."
        ),
        evidence=("doc-126#7", "doc-85#10"),
        delta=True,
        delta_semantics="related_not_equivalent",
        conditions=("document_comparison_requires_full_key",),
    ),
    frozenset({"R09", "R10"}): _verdict(
        RELATED_REQUIRES_EXPLANATION,
        "billing_mod_vs_cc_expenses",
        (
            "Faturamento×MOD (R09) e despesas por centro de custo "
            "(R10) são medidas distintas; vinculação possível por "
            "documento/produto — mas R09 não tem contrato "
            "implementado."
        ),
        evidence=("doc-126#7",),
    ),
    frozenset({"R12", "R15"}): _verdict(
        NOT_COMPARABLE,
        "state_vs_cutoff_process",
        (
            "R12 (estado de custo) e R15 (cutoff/processo) não "
            "possuem medida numérica comum — nenhum delta financeiro "
            "é válido."
        ),
        evidence=("doc-126#7",),
    ),
}


def classify_pair(
    rid_a: str,
    rid_b: str,
    *,
    measure: str | None = None,
    subject_filters_a: dict | None = None,
    subject_filters_b: dict | None = None,
) -> CompatibilityVerdict:
    """Classify a pair of reports for comparison.

    Same report → ``COMPARABLE`` under the conditions that keep the
    comparison honest (R10 universe must match — calculation and
    investigation totals are strict partitions, never blended).

    Different reports → the curated matrix; anything unlisted falls
    back to ``INSUFFICIENT_EVIDENCE``.
    """
    if rid_a == rid_b:
        if rid_a == "R10":
            uni_a = (subject_filters_a or {}).get(
                "universe", "calculation"
            )
            uni_b = (subject_filters_b or {}).get(
                "universe", "calculation"
            )
            if uni_a != uni_b:
                return _verdict(
                    NOT_COMPARABLE,
                    "r10_universe_mismatch",
                    (
                        "Os universos R10 'calculation' e "
                        "'investigation' são partições estritas — "
                        "comparar os totais como equivalentes mistura "
                        "o universo oficial com o investigativo."
                    ),
                    evidence=("doc-126#17", "doc-127#3"),
                )
        return _verdict(
            COMPARABLE,
            "same_report_same_convention",
            (
                "Mesmo relatório, mesma medida, mesma seleção e "
                "convenção de custo — variação por período/filial é "
                "diretamente comparável."
            ),
            evidence=("doc-126#7",),
            delta=True,
            delta_semantics="direct",
        )
    pair = _PAIR_MATRIX.get(frozenset({rid_a, rid_b}))
    if pair is None:
        return _verdict(
            INSUFFICIENT_EVIDENCE,
            "pair_not_classified",
            (
                "Par não classificado na matriz de compatibilidade — "
                "compatibilidade nunca é inferida por semelhança de "
                "colunas."
            ),
            evidence=("doc-126#7",),
        )
    return pair
