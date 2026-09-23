"""Forma canônica do item de material empenhado — compartilhada pelas rotas SD4."""

from __future__ import annotations


def normalize_operation_material_item(row: dict) -> dict:
    return {
        "product_code": text(row.get("product_code")),
        "description": text(row.get("description")),
        "unit": text(row.get("unit")),
        "product_type": text(row.get("product_type")).upper(),
        "original_qty": number(row.get("original_qty")),
        "open_qty": number(row.get("open_qty")),
        "consumed_qty": number(row.get("consumed_qty")),
        "commitment_count": int(row.get("commitment_count") or 0),
    }


def text(value: object) -> str:
    return str(value or "").strip()


def number(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
