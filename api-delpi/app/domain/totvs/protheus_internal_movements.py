"""Convenções Delpi — movimentações internas Protheus (SD3).

Classificação canônica domínio-owned dos fatos SD3:

- ``D3_DOC = 'INVENT'`` identifica o ajuste de inventário gerado pelo
  processamento da contagem SB7 (MATA270). A natureza vem do CF:
  ``DE0`` = ajuste de entrada (sobra); ``RE0`` = ajuste de saída
  (furo). O CF é consistente com o sinal do TM: a sobra usa
  ``TM 499`` (entrada) e o furo usa ``TM 999`` (saída).
- ``D3_CF = 'PR0'`` é entrada de produção.
- ``D3_CF`` ``DE0``/``RE0`` fora do documento ``INVENT`` é transferência
  entre armazéns (sai/entra).
- ``D3_TM = '999'`` com OP preenchida é consumo de produção (mesma
  convenção usada pelo consumo de estoque de segurança).
- Qualquer outro fato permanece ``unclassified`` — nunca inventar
  semântica para códigos desconhecidos.

Comprovado em dados (2026-10): todos os movimentos ``INVENT`` usam
apenas ``TM 499/CF DE0`` (sobra/entrada) e ``TM 999/CF RE0``
(furo/saída), sem estorno e sem quantidade negativa. A direção foi
validada contra o relatório Protheus de movimentações de inventário
(filial 02, 2026-09): as linhas ``TM 499/CF DE0`` somam exatamente a
coluna ENTRADAS e as ``TM 999/CF RE0`` somam exatamente a coluna
SAÍDAS — consistente com a regra Protheus ``TM < 500`` entrada /
``TM >= 500`` saída e com a semântica CF ``DE0``=devolução (entrada) /
``RE0``=requisição (saída). SB7 é apoio de proveniência
(não autoridade): a associação por filial+produto+armazém+data
apresentou alta correlação na base investigada (4.849/4.852
linhas 2025+), sem vínculo um-para-um garantido — documento e
quantidade contada só são expostos quando o documento candidato
é inequívoco (fail-closed).
"""

from __future__ import annotations

from dataclasses import dataclass

WAREHOUSE_TRANSFER_OUT_CF = "DE0"
WAREHOUSE_TRANSFER_IN_CF = "RE0"
WAREHOUSE_TRANSFER_CFS: tuple[str, ...] = (
    WAREHOUSE_TRANSFER_OUT_CF,
    WAREHOUSE_TRANSFER_IN_CF,
)

INVENTORY_ADJUSTMENT_DOCUMENT = "INVENT"
PRODUCTION_RECEIPT_CF = "PR0"
PRODUCTION_CONSUMPTION_TM = "999"

MOVEMENT_KIND_WAREHOUSE_TRANSFER = "warehouse_transfer"
MOVEMENT_KIND_INVENTORY_ADJUSTMENT = "inventory_adjustment"
MOVEMENT_KIND_PRODUCTION_RECEIPT = "production_receipt"
MOVEMENT_KIND_PRODUCTION_CONSUMPTION = "production_consumption"
KNOWN_MOVEMENT_KINDS: frozenset[str] = frozenset(
    {
        MOVEMENT_KIND_WAREHOUSE_TRANSFER,
        MOVEMENT_KIND_INVENTORY_ADJUSTMENT,
        MOVEMENT_KIND_PRODUCTION_RECEIPT,
        MOVEMENT_KIND_PRODUCTION_CONSUMPTION,
    }
)

MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER = "warehouse_transfer"
MOVEMENT_CATEGORY_PRODUCTION_RECEIPT = "production_receipt"
MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION = "production_consumption"
MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT = "inventory_adjustment"
MOVEMENT_CATEGORY_UNCLASSIFIED = "unclassified"

DIRECTION_INBOUND = "inbound"
DIRECTION_OUTBOUND = "outbound"

ADJUSTMENT_NATURE_SHORTAGE = "shortage"
ADJUSTMENT_NATURE_SURPLUS = "surplus"

_CATEGORY_LABELS: dict[str, str] = {
    MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER: "Transferência entre armazéns",
    MOVEMENT_CATEGORY_PRODUCTION_RECEIPT: "Entrada de produção",
    MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION: "Consumo de produção",
    MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT: "Ajuste de inventário",
    MOVEMENT_CATEGORY_UNCLASSIFIED: "Movimentação interna",
}


def _trim(value: object) -> str:
    return str(value or "").strip()


def movement_direction(tm: object) -> str | None:
    """Regra canônica de sinal SD3: TM < '500' entrada; TM >= '500' saída."""
    token = _trim(tm)
    if not token:
        return None
    return DIRECTION_INBOUND if token < "500" else DIRECTION_OUTBOUND


def classify_internal_movement(
    *,
    cf: object,
    tm: object,
    document: object,
    production_order: object,
) -> "MovementClassification":
    """Classifica um fato SD3 em categoria/direção semântica (fail-safe)."""
    cf_token = _trim(cf)
    doc_token = _trim(document)
    op_token = _trim(production_order)
    direction = movement_direction(tm)

    if doc_token == INVENTORY_ADJUSTMENT_DOCUMENT:
        # Natureza comprovada pelo CF contra o relatório Protheus:
        # DE0/TM 499 = ajuste de entrada (sobra), RE0/TM 999 = ajuste
        # de saída (furo). O CF é consistente com o sinal do TM.
        if cf_token == WAREHOUSE_TRANSFER_OUT_CF:
            nature = ADJUSTMENT_NATURE_SURPLUS
            adj_direction = DIRECTION_INBOUND
        elif cf_token == WAREHOUSE_TRANSFER_IN_CF:
            nature = ADJUSTMENT_NATURE_SHORTAGE
            adj_direction = DIRECTION_OUTBOUND
        else:
            nature = None
            adj_direction = direction
        return MovementClassification(
            category=MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT,
            direction=adj_direction,
            label=_CATEGORY_LABELS[MOVEMENT_CATEGORY_INVENTORY_ADJUSTMENT],
            inventory_adjustment_nature=nature,
        )
    if cf_token == PRODUCTION_RECEIPT_CF:
        return MovementClassification(
            category=MOVEMENT_CATEGORY_PRODUCTION_RECEIPT,
            direction=DIRECTION_INBOUND,
            label=_CATEGORY_LABELS[MOVEMENT_CATEGORY_PRODUCTION_RECEIPT],
            inventory_adjustment_nature=None,
        )
    if cf_token in WAREHOUSE_TRANSFER_CFS:
        return MovementClassification(
            category=MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER,
            direction=(
                DIRECTION_OUTBOUND
                if cf_token == WAREHOUSE_TRANSFER_OUT_CF
                else DIRECTION_INBOUND
            ),
            label=_CATEGORY_LABELS[MOVEMENT_CATEGORY_WAREHOUSE_TRANSFER],
            inventory_adjustment_nature=None,
        )
    if _trim(tm) == PRODUCTION_CONSUMPTION_TM and op_token:
        return MovementClassification(
            category=MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION,
            direction=direction,
            label=_CATEGORY_LABELS[MOVEMENT_CATEGORY_PRODUCTION_CONSUMPTION],
            inventory_adjustment_nature=None,
        )
    return MovementClassification(
        category=MOVEMENT_CATEGORY_UNCLASSIFIED,
        direction=direction,
        label=_CATEGORY_LABELS[MOVEMENT_CATEGORY_UNCLASSIFIED],
        inventory_adjustment_nature=None,
    )


@dataclass(frozen=True, slots=True)
class MovementClassification:
    category: str
    direction: str | None
    label: str
    inventory_adjustment_nature: str | None


def movement_kind_filters(kind: str | None) -> dict[str, object] | None:
    """Predicados do recorte `kind` — espec declarativa consumida pelo SQL.

    None = universo SD3 completo. Chaves suportadas:
    ``cf_in``, ``cf_eq``, ``doc_eq``, ``doc_ne``, ``tm_eq``,
    ``requires_production_order``.
    """
    normalized = (kind or "").strip().lower()
    if not normalized:
        return None
    if normalized == MOVEMENT_KIND_WAREHOUSE_TRANSFER:
        return {
            "cf_in": WAREHOUSE_TRANSFER_CFS,
            "doc_ne": INVENTORY_ADJUSTMENT_DOCUMENT,
        }
    if normalized == MOVEMENT_KIND_INVENTORY_ADJUSTMENT:
        return {"doc_eq": INVENTORY_ADJUSTMENT_DOCUMENT}
    if normalized == MOVEMENT_KIND_PRODUCTION_RECEIPT:
        return {"cf_eq": PRODUCTION_RECEIPT_CF}
    if normalized == MOVEMENT_KIND_PRODUCTION_CONSUMPTION:
        return {
            "tm_eq": PRODUCTION_CONSUMPTION_TM,
            "doc_ne": INVENTORY_ADJUSTMENT_DOCUMENT,
            "requires_production_order": True,
        }
    raise ValueError("kind de movimentação interna inválido.")
