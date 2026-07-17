"""meta.sections[] para respostas composite_analysis (Fase 6)."""

from __future__ import annotations

from typing import Any

SECTION_LABELS: dict[str, str] = {
    "structure": "Estrutura",
    "guide": "Roteiro",
    "inspection": "Inspeção",
    "raw_material_stock": "Estoque de MPs",
    "production": "Produção",
    "shipping": "Expedição",
    "materials": "Impacto de MPs",
    "summary": "Resumo de custos",
    "simulation": "Simulação",
    "last_purchase": "Última compra",
    "budget_history": "Histórico de orçamento",
    "price_history": "Histórico de preço",
    "price_variation": "Variação de preço",
    "open_purchase_orders": "Pedidos de compra em aberto",
    "open_commitments": "Empenhos em aberto",
    "stock_projection": "Extrato projetado de saldo",
    "linked_suppliers": "Fornecedores vinculados",
}


def _item_count(block: dict[str, Any]) -> int:
    total = block.get("total")

    if total is not None:
        try:
            return int(total)
        except (TypeError, ValueError):
            pass

    items = block.get("items")

    if isinstance(items, list):
        return len(items)

    return 0


def _is_truncated(block: dict[str, Any], *, view: str) -> bool:
    if view == "summary":
        return True

    if block.get("truncated") is True:
        return True

    items = block.get("items")

    if not isinstance(items, list):
        return False

    total = block.get("total")

    if total is None:
        return False

    try:
        return len(items) < int(total)
    except (TypeError, ValueError):
        return False


def build_composite_sections(
    data: dict[str, Any],
    *,
    view: str = "full",
    section_keys: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    keys = section_keys or tuple(SECTION_LABELS.keys())
    sections: list[dict[str, Any]] = []

    for key in keys:
        block = data.get(key)

        if not isinstance(block, dict):
            continue

        sections.append(
            {
                "key": key,
                "label": SECTION_LABELS.get(key, key),
                "itemCount": _item_count(block),
                "truncated": _is_truncated(block, view=view),
            }
        )

    return sections
