"""Pendências de ruptura, projetadas pelo provider oficial Delpi Reports.

Não recalcula estoque de segurança nem empenhos; apenas normaliza, filtra
filial e datas e mescla os alertas na cronologia de ações da Gestão à Vista.
"""
from __future__ import annotations

from datetime import date, timedelta
from math import isfinite
from typing import Any, Iterable, Mapping

RUPTURE_KIND = "stock_rupture"
OP_KIND = "include_production_order"
_UNKNOWN_SORT_DATE = "9999-12-31"


def _quantity(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    return number if isfinite(number) else None


def _event_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def build_stock_rupture_pendencies(
    rows: Iterable[Mapping[str, Any]],
    *,
    branch: str,
    today: date,
    horizon_days: int = 30,
) -> list[dict[str, Any]]:
    """Uma ruptura por material/filial, mesmo para eventos já vencidos.

    O provider já filtra saldo projetado negativo. Mantemos um segundo filtro
    defensivo: nenhuma linha de outra filial, sem data ou fora da janela.
    """
    last_day = today + timedelta(days=horizon_days)
    by_material: dict[str, dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, Mapping) or str(raw.get("branch") or "").strip() != branch:
            continue
        product_code = str(raw.get("product_code") or "").strip()
        first_date = _event_date(raw.get("first_shortage_date"))
        if not product_code or first_date is None or first_date > last_day:
            continue
        item = {
            "id": f"{branch}|stock-rupture|{product_code}",
            "kind": RUPTURE_KIND,
            "branch": branch,
            "product_code": product_code,
            "product_description": str(raw.get("product_description") or "").strip(),
            "unit": str(raw.get("unit") or "").strip().upper(),
            "first_shortage_date": first_date.isoformat(),
            "available_stock": _quantity(raw.get("available_stock")),
            "shortage_balance": _quantity(raw.get("shortage_balance")),
            "next_purchase": str(raw.get("next_purchase") or "").strip(),
            "observation": str(raw.get("observation") or "").strip(),
            "last_inventory_date": (
                _event_date(raw.get("last_inventory_date")).isoformat()
                if _event_date(raw.get("last_inventory_date"))
                else None
            ),
            "provider_key": "safety_stock_shortage_30d",
        }
        previous = by_material.get(product_code)
        if previous is None or item["first_shortage_date"] < previous["first_shortage_date"]:
            by_material[product_code] = item
    return sorted(
        by_material.values(), key=lambda item: (item["first_shortage_date"], item["product_code"])
    )


def merge_pendency_items(
    op_items: Iterable[Mapping[str, Any]],
    rupture_items: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Ordenação única: OP pela sugestão D-2, ruptura pela data efetiva.

    Ruptura tem prioridade sobre inclusão de OP em empate de datas.
    Não agrega produtos de naturezas distintas só porque os códigos coincidem.
    """
    items = [dict(item) for item in (*op_items, *rupture_items)]
    return sorted(
        items,
        key=lambda item: (
            item.get("first_shortage_date")
            if item.get("kind") == RUPTURE_KIND
            else item.get("suggested_op_date") or _UNKNOWN_SORT_DATE,
            0 if item.get("kind") == RUPTURE_KIND else 1,
            str(item.get("product_code") or ""),
            str(item.get("id") or ""),
        ),
    )
