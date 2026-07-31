"""Aliases canônicos em itens de OP (SC2 / OTD) — sem remover chaves legadas."""

from __future__ import annotations

from typing import Any


class ProductionOrderItemAliasService:
    """Espelha campos canônicos sem breaking change."""

    @classmethod
    def enrich_list_item(cls, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return item
        out = dict(item)
        description = out.get("description")
        product_description = out.get("product_description")
        if product_description and not description:
            out["description"] = product_description
        elif description and not product_description:
            out["product_description"] = description

        if "pending_qty" not in out:
            planned = out.get("planned_qty")
            produced = out.get("produced_qty")
            if planned is not None and produced is not None:
                try:
                    out["pending_qty"] = float(planned) - float(produced)
                except (TypeError, ValueError):
                    pass

        status = out.get("status")
        otd_status = out.get("otd_status")
        if otd_status and not status:
            out["status"] = otd_status
        elif status and not otd_status:
            out["otd_status"] = status

        days_diff = out.get("days_diff")
        days_late = out.get("days_late")
        if days_late is None and days_diff is not None:
            out["days_late"] = days_diff
        elif days_diff is None and days_late is not None:
            out["days_diff"] = days_late

        return out

    @classmethod
    def enrich_items(cls, items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if not items:
            return []
        return [cls.enrich_list_item(item) or item for item in items]
