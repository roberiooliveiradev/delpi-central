"""Mapper — linhas do diff (conjunto x componente) → item canônico por conjunto.

A consulta devolve uma linha por componente divergente para não voltar ao banco
atrás do detalhe; aqui essas linhas viram um item por conjunto, com as listas de
componentes faltando e sobrando.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value: Any) -> str | None:
    """Aceita YYYYMMDD (Protheus) e date/datetime/ISO (view PCP)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) == 8:
        if text == "00000000":
            return None
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10] or None


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _as_bool(value: Any) -> bool:
    return _as_int(value) == 1


class ProductionOrderSetMapper:
    @classmethod
    def _set_key(cls, row: dict[str, Any]) -> tuple[str, str, str]:
        return (
            _clean(row.get("branch")),
            _clean(row.get("set_number")),
            _clean(row.get("set_item")),
        )

    @classmethod
    def _new_item(cls, row: dict[str, Any]) -> dict[str, Any]:
        branch, set_number, set_item = cls._set_key(row)
        return {
            "branch": branch,
            "set_number": set_number,
            "set_item": set_item,
            "set_key": f"{set_number}{set_item}",
            "root_code": _clean(row.get("root_code")),
            "root_description": _clean(row.get("root_description")),
            "root_type": _clean(row.get("root_type")),
            "root_order": _clean(row.get("root_order_key")),
            "due_date": _iso_date(row.get("due_date")),
            "issued_at": _iso_date(row.get("reference_date")),
            "order_count": _as_int(row.get("order_count")),
            "open_order_count": _as_int(row.get("open_order_count")),
            "expected_component_count": _as_int(row.get("expected_component_count")),
            "created_component_count": _as_int(row.get("created_component_count")),
            "missing_count": _as_int(row.get("missing_count")),
            "extra_count": _as_int(row.get("extra_count")),
            "missing_components": [],
            "extra_components": [],
        }

    @classmethod
    def _component(cls, row: dict[str, Any], *, include_order: bool) -> dict[str, Any]:
        component = {
            "product_code": _clean(row.get("component_code")),
            "description": _clean(row.get("component_description")),
            "product_type": _clean(row.get("component_type")),
        }
        if include_order:
            component["production_order"] = _clean(row.get("component_order_key"))
        else:
            component["bom_level"] = _as_int(row.get("bom_level"))
        return component

    @classmethod
    def map_sets(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in rows:
            key = cls._set_key(row)
            item = items.get(key)
            if item is None:
                item = cls._new_item(row)
                items[key] = item

            code = _clean(row.get("component_code"))
            if not code:
                continue
            if _as_bool(row.get("is_missing")):
                item["missing_components"].append(
                    cls._component(row, include_order=False)
                )
            elif _as_bool(row.get("is_extra")):
                item["extra_components"].append(cls._component(row, include_order=True))

        return list(items.values())

    @classmethod
    def map_summary(cls, row: dict[str, Any] | None) -> dict[str, Any]:
        row = row or {}
        return {
            "checked_set_count": _as_int(row.get("checked_set_count")),
            "incomplete_set_count": _as_int(row.get("incomplete_set_count")),
            "missing_set_count": _as_int(row.get("missing_set_count")),
            "extra_set_count": _as_int(row.get("extra_set_count")),
        }
