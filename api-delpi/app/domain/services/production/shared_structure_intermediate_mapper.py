"""Mapper — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from typing import Any


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class SharedStructureIntermediateMapper:
    @classmethod
    def map_items(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: dict[str, dict[str, Any]] = {}
        for row in rows:
            code = _clean(row.get("component_code"))
            if not code:
                continue
            item = items.get(code)
            if item is None:
                item = {
                    "intermediate_code": code,
                    "intermediate_description": _clean(row.get("component_description")),
                    "intermediate_type": _clean(row.get("component_type")),
                    "shared_pa_count": _as_int(row.get("shared_pa_count")),
                    "finished_products": [],
                }
                items[code] = item

            pa_code = _clean(row.get("pa_code"))
            if not pa_code:
                continue
            existing = {
                fp["product_code"]
                for fp in item["finished_products"]
                if isinstance(fp, dict)
            }
            if pa_code in existing:
                continue
            item["finished_products"].append(
                {
                    "product_code": pa_code,
                    "description": _clean(row.get("pa_description")),
                    "bom_level": _as_int(row.get("bom_level")),
                }
            )

        return list(items.values())

    @classmethod
    def map_summary(cls, row: dict[str, Any] | None) -> dict[str, Any]:
        row = row or {}
        return {
            "checked_pa_count": _as_int(row.get("checked_pa_count")),
            "shared_intermediate_count": _as_int(row.get("shared_intermediate_count")),
            "max_shared_pa_count": _as_int(row.get("max_shared_pa_count")),
        }
