"""Convenções Delpi — movimentações internas Protheus (SD3.D3_CF).

Transferência entre armazéns usa classificação DE0 (sai) e RE0 (entra).
PR0 é entrada de produção; TM 999 é baixa de consumo — ficam de fora deste recorte.
"""

from __future__ import annotations

WAREHOUSE_TRANSFER_OUT_CF = "DE0"
WAREHOUSE_TRANSFER_IN_CF = "RE0"
WAREHOUSE_TRANSFER_CFS: tuple[str, ...] = (
    WAREHOUSE_TRANSFER_OUT_CF,
    WAREHOUSE_TRANSFER_IN_CF,
)

MOVEMENT_KIND_WAREHOUSE_TRANSFER = "warehouse_transfer"
KNOWN_MOVEMENT_KINDS: frozenset[str] = frozenset({MOVEMENT_KIND_WAREHOUSE_TRANSFER})


def warehouse_transfer_cfs_for_kind(kind: str | None) -> tuple[str, ...] | None:
    """Devolve os CFs do recorte, ou None quando o universo SD3 permanece completo."""
    normalized = (kind or "").strip().lower()
    if not normalized:
        return None
    if normalized != MOVEMENT_KIND_WAREHOUSE_TRANSFER:
        raise ValueError("kind de movimentação interna inválido.")
    return WAREHOUSE_TRANSFER_CFS
