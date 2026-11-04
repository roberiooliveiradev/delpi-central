"""Validação do envelope ``POST /production/orders/operation-materials/batch``.

Fonte canônica da distinção entre ausência legítima de empenhos SD4 e resposta
incompleta/inválida da integração. Consumida pelo resolvedor de sequenciamento e
pela prévia de materiais do Alimentador — sem inventar indicador de completude
além do que o contrato já expõe.
"""

from __future__ import annotations

from typing import Any, Sequence

from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
)
from production_control_app.domain.services.sequencing_material_resolution import (
    _count,
)


def validated_operation_materials_batch_items(
    payload: Any, *, branch: str, requested: Sequence[str]
) -> list[dict[str, Any]] | None:
    """Extrai ``items`` só se a resposta for íntegra; ``None`` = malformada.

    Validação integral: envelope dict que não declare ``success: false``,
    lista ``items`` coerente com ``summary.returned_count`` quando presente,
    filial do envelope e das linhas coerente com a pedida, toda linha é dict
    com OP presente e pertencente ao conjunto solicitado. ``items: []`` é
    resposta válida (OPs sem empenho), não confundir com resposta quebrada.

    ``returned_count = 0`` **não** é falha — é ausência legítima de linhas.
    Quando ``production_orders`` é ecoado, todas as OPs pedidas devem aparecer.
    Nenhum registro é descartado silenciosamente — um item estranho invalida
    o lote inteiro.
    """
    if not isinstance(payload, dict):
        return None
    if payload.get("success") is False:
        return None
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload
    rows = source.get("items") if isinstance(source, dict) else None
    if not isinstance(rows, list):
        return None

    summary = source.get("summary")
    if isinstance(summary, dict) and "returned_count" in summary:
        declared = _count(summary.get("returned_count"))
        if declared is None or declared != len(rows):
            return None

    if str(source.get("branch") or "").strip() and (
        str(source.get("branch")).strip() != branch
    ):
        return None

    echoed = source.get("production_orders")
    if isinstance(echoed, list):
        covered = {normalize_order_code(order) for order in echoed}
        if any(normalize_order_code(order) not in covered for order in requested):
            return None

    wanted = {normalize_order_code(order) for order in requested}
    items: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        order = normalize_order_code(row.get("production_order"))
        if not order or order not in wanted:
            return None
        row_branch = str(row.get("branch") or "").strip()
        if row_branch and row_branch != branch:
            return None
        items.append(row)
    return items
