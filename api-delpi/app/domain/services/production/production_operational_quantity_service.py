"""Conversão canônica de quantidades operacionais (OP/apontamento) para unidade de exibição."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.services.product.product_playbook_numeric_service import (
    ProductPlaybookNumericService,
)

_CONTENT_PATH = (
    Path(__file__).resolve().parents[3]
    / "content"
    / "production_operational_units.json"
)


@dataclass(frozen=True)
class ProductionOperationalUnitProfile:
    catalog_unit: str | None
    display_unit_factor: float
    display_unit: str | None

    def converts_catalog_unit(self) -> bool:
        return self.display_unit_factor not in (0, 1)


class ProductionOperationalQuantityService:
    """Quantidades de OP/apontamento em MI (C2_UM / B1_UM) → peças (UN) na resposta."""

    @classmethod
    def resolve(cls, unit: str | None) -> ProductionOperationalUnitProfile:
        normalized = str(unit or "").strip().upper()
        bundle = cls._bundle()
        default = bundle.get("default") if isinstance(bundle.get("default"), dict) else {}
        units = bundle.get("units") if isinstance(bundle.get("units"), dict) else {}
        profile = units.get(normalized) if normalized else None

        if not isinstance(profile, dict):
            profile = default

        catalog_unit = str(profile.get("catalogUnit") or normalized or "").strip() or None
        display_unit = profile.get("displayUnit")
        if display_unit is not None:
            display_unit = str(display_unit).strip() or None

        return ProductionOperationalUnitProfile(
            catalog_unit=catalog_unit,
            display_unit_factor=float(
                profile.get("displayUnitFactor") or default.get("displayUnitFactor") or 1
            ),
            display_unit=display_unit,
        )

    @classmethod
    def quantity_fields(cls) -> tuple[str, ...]:
        bundle = cls._bundle()
        raw = bundle.get("quantityFields")
        if not isinstance(raw, list):
            return (
                "planned_qty",
                "produced_qty",
                "pending_qty",
                "order_planned_qty",
                "order_produced_qty",
                "lost_qty",
            )
        return tuple(str(field).strip() for field in raw if str(field).strip())

    @classmethod
    def convert_quantity(cls, quantity: object, unit: str | None) -> float:
        profile = cls.resolve(unit)
        if not profile.converts_catalog_unit():
            return ProductPlaybookNumericService.to_float(quantity)

        return ProductPlaybookNumericService.to_float(quantity) * profile.display_unit_factor

    @classmethod
    def normalize_item(cls, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            return item

        unit = cls._resolve_item_unit(item)
        profile = cls.resolve(unit)
        if not profile.converts_catalog_unit():
            return dict(item)

        normalized = dict(item)
        for field in cls.quantity_fields():
            if field not in normalized:
                continue
            normalized[field] = cls.convert_quantity(normalized[field], unit)

        if profile.display_unit:
            normalized["unit"] = profile.display_unit

        return normalized

    @classmethod
    def normalize_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.normalize_item(item) for item in items]

    @staticmethod
    def _resolve_item_unit(item: dict[str, Any]) -> str | None:
        for key in ("unit", "product_unit", "order_unit"):
            value = item.get(key)
            if value not in (None, ""):
                return str(value).strip() or None
        return None

    @classmethod
    @lru_cache(maxsize=1)
    def _bundle(cls) -> dict[str, Any]:
        with _CONTENT_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, dict) else {}
