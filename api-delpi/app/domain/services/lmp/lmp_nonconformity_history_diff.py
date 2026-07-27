"""Diff de campos para histórico de NCs LMP."""

from __future__ import annotations

from typing import Any

FIELD_LABELS: dict[str, str] = {
    "status": "Status",
    "sale_number": "OV",
    "lmp_number": "Número da LMP",
    "customer_name": "Cliente",
    "occurrence_date": "Data de ocorrência",
    "launch_date": "Data de lançamento",
    "last_revision_date": "Última revisão",
    "executed_by": "Executou",
    "released_by": "Liberou",
    "defect_description": "Descrição do problema",
    "corrective_actions": "Ações corretivas",
    "technical_opinion": "Parecer técnico",
    "problem_tags": "Problema identificado",
    "products": "Produtos",
}

_TRACKED_SCALAR = (
    "status",
    "sale_number",
    "lmp_number",
    "customer_name",
    "occurrence_date",
    "launch_date",
    "last_revision_date",
    "executed_by",
    "released_by",
    "defect_description",
    "corrective_actions",
    "technical_opinion",
)


def _norm_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        label = _norm_text(item)
        if not label:
            continue
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def _norm_products(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, dict):
            continue
        code = _norm_text(raw.get("product_code") or raw.get("code"))
        if not code:
            continue
        key = code.upper()
        if key in seen:
            continue
        seen.add(key)
        description = _norm_text(
            raw.get("product_description") or raw.get("description")
        )
        out.append(
            {
                "product_code": key,
                "product_description": description or "",
            }
        )
    out.sort(key=lambda item: item["product_code"])
    return out


def _values_equal(left: Any, right: Any) -> bool:
    return left == right


def build_nc_history_changes(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Monta payload ``changes`` com lista de campos alterados.

    ``before`` nulo → criação (lista os valores iniciais não vazios).
    """
    previous = before or {}
    current = after or {}
    fields: list[dict[str, Any]] = []

    for key in _TRACKED_SCALAR:
        old = _norm_text(previous.get(key))
        new = _norm_text(current.get(key))
        if before is None:
            if new is None:
                continue
            fields.append(
                {
                    "field": key,
                    "label": FIELD_LABELS[key],
                    "old": None,
                    "new": new,
                }
            )
            continue
        if not _values_equal(old, new):
            fields.append(
                {
                    "field": key,
                    "label": FIELD_LABELS[key],
                    "old": old,
                    "new": new,
                }
            )

    old_tags = _norm_tags(previous.get("problem_tags"))
    new_tags = _norm_tags(current.get("problem_tags"))
    if before is None:
        if new_tags:
            fields.append(
                {
                    "field": "problem_tags",
                    "label": FIELD_LABELS["problem_tags"],
                    "old": None,
                    "new": new_tags,
                }
            )
    elif old_tags != new_tags:
        fields.append(
            {
                "field": "problem_tags",
                "label": FIELD_LABELS["problem_tags"],
                "old": old_tags,
                "new": new_tags,
            }
        )

    old_products = _norm_products(previous.get("products"))
    new_products = _norm_products(current.get("products"))
    if before is None:
        if new_products:
            fields.append(
                {
                    "field": "products",
                    "label": FIELD_LABELS["products"],
                    "old": None,
                    "new": new_products,
                }
            )
    elif old_products != new_products:
        fields.append(
            {
                "field": "products",
                "label": FIELD_LABELS["products"],
                "old": old_products,
                "new": new_products,
            }
        )

    return {"fields": fields}
