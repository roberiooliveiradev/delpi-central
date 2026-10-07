"""Ajustes de inventário — regra canônica Delpi (SD3 doc='INVENT' + SB7).

Comprovado em dados (out/2026):

- O processamento da contagem física (SB7, origem MATA270, B7_STATUS='2')
  grava a diferença em SD3 com ``D3_DOC = 'INVENT'``.
- Só existem dois pares TM/CF nesse documento: ``TM 999/CF RE0`` =
  ajuste positivo (sobra) e ``TM 499/CF DE0`` = ajuste negativo (furo).
- A natureza é autoridade do CF: ``RE0`` = entrada (sobra);
  ``DE0`` = saída (furo). O TM **não** é autoridade para ajuste —
  a sobra é gravada com ``TM 999`` (também usado no consumo).
- ``D3_CUSTO1`` é o valor **total do movimento** na moeda 1 no momento
  do ajuste, não custo unitário a multiplicar por ``D3_QUANT`` (mesma
  interpretação do cálculo histórico SB9+SD3, que aplica ``D3_CUSTO1``
  diretamente ao movimento).
- ``D3_TPMOVAJ`` não é usado no ambiente; SF5 não contém os TM 499/999;
  F0Q vazio; C5D é cadastro fiscal sem vínculo comprovado.
- SB7 é apoio de proveniência, não autoridade: a associação
  SB7↔SD3 por filial + produto + armazém + data apresentou
  alta correlação na base investigada (4.849/4.852 linhas 2025+),
  mas isso não estabelece vínculo um-para-um autoritativo.
  `inventory_document`/`counted_quantity` só são expostos quando
  existe exatamente um documento candidato; ausente ou ambíguo
  → fail-closed (None).

As expressões SQL abaixo são a única fonte da classificação — o mesmo
padrão de ``ConsumptionRealQuantityService``: o domínio possui a regra
e o repositório a referencia, sem duplicar condições.
"""

from __future__ import annotations

from app.domain.totvs.protheus_internal_movements import (
    ADJUSTMENT_NATURE_SHORTAGE,
    ADJUSTMENT_NATURE_SURPLUS,
    INVENTORY_ADJUSTMENT_DOCUMENT,
)

NATURE_SHORTAGE = ADJUSTMENT_NATURE_SHORTAGE
NATURE_SURPLUS = ADJUSTMENT_NATURE_SURPLUS
KNOWN_NATURES: frozenset[str] = frozenset({NATURE_SHORTAGE, NATURE_SURPLUS})

NATURE_LABELS: dict[str, str] = {
    NATURE_SHORTAGE: "Furo de inventário",
    NATURE_SURPLUS: "Sobra de inventário",
}


class InventoryAdjustmentClassification:
    """Expressões SQL canônicas do ajuste de inventário (alias SD3)."""

    # Natureza comprovada pelo CF: RE0 = sobra (entrada); DE0 = furo (saída).
    NATURE_SQL_EXPRESSION = f"""
        CASE
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN '{NATURE_SURPLUS}'
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN '{NATURE_SHORTAGE}'
          ELSE 'other'
        END
    """

    # Quantidade/valor assinados: sobra positiva, furo negativa.
    SIGNED_QUANTITY_SQL_EXPRESSION = """
        CASE
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN SD3.D3_QUANT
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN -SD3.D3_QUANT
          ELSE SD3.D3_QUANT
        END
    """
    SIGNED_VALUE_SQL_EXPRESSION = """
        CASE
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN SD3.D3_CUSTO1
          WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN -SD3.D3_CUSTO1
          ELSE SD3.D3_CUSTO1
        END
    """


def normalize_nature(value: str | None) -> str | None:
    token = (value or "").strip().lower()
    if not token:
        return None
    if token not in KNOWN_NATURES:
        raise ValueError("nature deve ser 'shortage' ou 'surplus'.")
    return token


def nature_label(nature: str | None) -> str:
    return NATURE_LABELS.get(str(nature or "").strip(), "Ajuste de inventário")


def resolve_inventory_provenance(
    candidate_document_count: object,
    document: object,
    counted_quantity: object,
) -> tuple[object, object]:
    """Proveniência SB7 fail-closed — decisão canônica do ajuste.

    SB7 é apoio de proveniência, não autoridade: o documento de
    inventário só é exposto quando existe **exatamente um** documento
    candidato (não nulo, não deletado) para a chave
    filial+produto+armazém+data. Zero ou múltiplos candidatos
    → (None, None), nunca TOP 1/MIN/MAX como autoridade.
    """
    try:
        count = int(candidate_document_count or 0)
    except (TypeError, ValueError):
        count = 0
    if count != 1:
        return None, None
    return document, counted_quantity


INVENTORY_ADJUSTMENT_DOC = INVENTORY_ADJUSTMENT_DOCUMENT
