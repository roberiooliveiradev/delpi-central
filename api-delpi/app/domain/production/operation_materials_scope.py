"""Escopo — empenhos de material por OP e operação (SD4010).

O empenho é a única fonte de "o que esta operação consome": a ``SD4010`` guarda
o vínculo material × OP × operação (``D4_OP``, ``D4_OPERAC``, ``D4_COD``) com a
quantidade original (``D4_QTDEORI``) e o saldo ainda em aberto (``D4_QUANT``).

A estrutura vigente (``SG1010``) **não** substitui o empenho: ela descreve o
produto, não o que foi reservado para a ordem já aberta.
"""

from __future__ import annotations

from collections.abc import Iterable

OPERATION_MATERIALS_COMMITMENT_TABLE = "SD4010"
OPERATION_MATERIALS_PRODUCT_TABLE = "SB1010"

# Teto de OPs por requisição em lote. Existe para o consumidor paginar a própria
# janela em vez de montar um IN sem limite no SQL Server.
MAX_BATCH_PRODUCTION_ORDERS = 300


def normalize_production_orders(orders: Iterable[object]) -> tuple[str, ...]:
    """Normaliza a lista de OPs preservando a ordem pedida e removendo repetidas.

    Estourar o teto é erro do chamador, não motivo para truncar em silêncio:
    devolver menos empenhos do que a janela pede faria o consumidor subestimar
    a necessidade de material.
    """
    normalized: list[str] = []
    seen: set[str] = set()

    for raw in orders or ():
        code = str(raw or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        normalized.append(code)

    if len(normalized) > MAX_BATCH_PRODUCTION_ORDERS:
        raise ValueError(
            "production_orders excede o limite de "
            f"{MAX_BATCH_PRODUCTION_ORDERS} OPs por requisição."
        )

    return tuple(normalized)
