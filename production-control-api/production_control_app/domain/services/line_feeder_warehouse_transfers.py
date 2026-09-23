"""Empilha saídas e entradas de transferência entre armazéns.

A api-delpi lista linhas SD3; o alimentador precisa do par origem→destino.
Classificação Delpi: DE0 sai, RE0 entra. Consumo e produção ficam de fora.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

WAREHOUSE_TRANSFER_OUT_CF = "DE0"
WAREHOUSE_TRANSFER_IN_CF = "RE0"
WAREHOUSE_TRANSFER_CFS = frozenset(
    {WAREHOUSE_TRANSFER_OUT_CF, WAREHOUSE_TRANSFER_IN_CF}
)
MOVEMENT_KIND_WAREHOUSE_TRANSFER = "warehouse_transfer"


def pair_warehouse_transfers(
    rows: Sequence[Mapping[str, Any]],
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Agrupa DE0+RE0 do mesmo documento, data e produto.

    Linha órfã permanece com um lado vazio. Ordem: emissão mais recente primeiro.
    """
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []

    for row in rows:
        cf = _text(row.get("cf")).upper()
        if cf not in WAREHOUSE_TRANSFER_CFS:
            continue
        key = (
            _text(row.get("document")),
            _issued_at(row),
            _text(row.get("product_code")),
        )
        entry = grouped.get(key)
        if entry is None:
            entry = {
                "issued_at": key[1],
                "document": key[0],
                "from_warehouse": "",
                "to_warehouse": "",
                "quantity": None,
                "user_name": "",
            }
            grouped[key] = entry
            order.append(key)

        warehouse = _text(row.get("location"))
        quantity = _quantity(row.get("quantity"))
        user_name = _text(row.get("user_name"))
        if cf == WAREHOUSE_TRANSFER_OUT_CF:
            if not entry["from_warehouse"]:
                entry["from_warehouse"] = warehouse
            if entry["quantity"] is None:
                entry["quantity"] = quantity
        else:
            if not entry["to_warehouse"]:
                entry["to_warehouse"] = warehouse
            if entry["quantity"] is None:
                entry["quantity"] = quantity
        if user_name and not entry["user_name"]:
            entry["user_name"] = user_name

    items = [grouped[key] for key in order]
    items.sort(key=lambda item: item["issued_at"], reverse=True)
    cap = max(int(limit), 0)
    return items[:cap] if cap else items


def _issued_at(row: Mapping[str, Any]) -> str:
    return _text(row.get("issued_at") or row.get("issue_date"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _quantity(value: Any) -> float:
    try:
        return round(abs(float(value or 0)), 6)
    except (TypeError, ValueError):
        return 0.0
