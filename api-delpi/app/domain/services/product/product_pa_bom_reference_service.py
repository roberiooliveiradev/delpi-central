"""Referência canônica de BOM — necessidade de MP sempre para 1 PA."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = (
    Path(__file__).resolve().parents[3]
    / "content"
    / "product_pa_bom_reference.json"
)


@dataclass(frozen=True)
class ProductPaBomReference:
    reference_quantity: float
    reference_unit: str
    catalog_unit: str | None
    catalog_quantity_per_reference: float
    bom_quantity_factor: float

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "reference_quantity": self.reference_quantity,
            "reference_unit": self.reference_unit,
            "bom_quantity_factor": self.bom_quantity_factor,
        }

        if self.catalog_unit:
            payload["catalog_unit"] = self.catalog_unit
            payload["catalog_quantity_per_reference"] = self.catalog_quantity_per_reference

        return payload


class ProductPaBomReferenceService:
    """Quantidades de estrutura/estoque expressas para montar 1 PA (não rótulo MI)."""

    @classmethod
    def resolve(cls, product_unit: str | None) -> ProductPaBomReference:
        normalized = str(product_unit or "").strip().upper()
        bundle = cls._bundle()
        default = bundle.get("default") if isinstance(bundle.get("default"), dict) else {}
        units = bundle.get("units") if isinstance(bundle.get("units"), dict) else {}
        profile = units.get(normalized) if normalized else None

        if not isinstance(profile, dict):
            profile = default

        catalog_unit = str(profile.get("catalogUnit") or normalized or "").strip() or None

        return ProductPaBomReference(
            reference_quantity=float(profile.get("referenceQuantity") or default.get("referenceQuantity") or 1),
            reference_unit=str(profile.get("referenceUnit") or default.get("referenceUnit") or "PA"),
            catalog_unit=catalog_unit,
            catalog_quantity_per_reference=float(
                profile.get("catalogQuantityPerReference")
                or profile.get("referenceQuantity")
                or default.get("referenceQuantity")
                or 1
            ),
            bom_quantity_factor=float(
                profile.get("bomQuantityFactor") or default.get("bomQuantityFactor") or 1
            ),
        )

    @classmethod
    def resolve_from_product(cls, product: dict[str, Any] | None) -> ProductPaBomReference:
        if not isinstance(product, dict):
            return cls.resolve(None)

        return cls.resolve(str(product.get("unit") or "").strip() or None)

    @classmethod
    def quantity_required_for_one_pa(cls, raw_quantity: object, product_unit: str | None) -> float:
        try:
            quantity = float(raw_quantity or 0)
        except (TypeError, ValueError):
            return 0.0

        reference = cls.resolve(product_unit)

        return quantity * reference.bom_quantity_factor

    @classmethod
    def has_stock_for_one_pa(cls, *, available_quantity: object, required_quantity: float) -> str:
        try:
            available = float(available_quantity or 0)
        except (TypeError, ValueError):
            available = 0.0

        if required_quantity <= 0:
            return "SIM"

        return "SIM" if available >= required_quantity else "NAO"

    @classmethod
    def pa_producible_from_stock(
        cls,
        *,
        available_quantity: object,
        required_quantity: object,
    ) -> float | None:
        try:
            required = float(required_quantity or 0)
        except (TypeError, ValueError):
            return None

        if required <= 0:
            return None

        try:
            available = float(available_quantity or 0)
        except (TypeError, ValueError):
            available = 0.0

        return available / required

    @classmethod
    def summarize_pa_producible_capacity(cls, materials: list[dict[str, Any]]) -> dict[str, Any]:
        coverage_rows: list[dict[str, Any]] = []
        limits: list[tuple[float, dict[str, Any]]] = []

        for material in materials:
            if not isinstance(material, dict):
                continue

            required = material.get("quantity_required_for_one_pa")
            available = material.get("available_quantity")
            producible = cls.pa_producible_from_stock(
                available_quantity=available,
                required_quantity=required,
            )

            row = dict(material)

            if producible is None:
                row["pa_producible_from_stock"] = None
            else:
                from app.domain.services.product.product_playbook_numeric_service import (
                    ProductPlaybookNumericService,
                )

                formatted = ProductPlaybookNumericService.format_quantity(producible)
                row["pa_producible_from_stock"] = formatted
                limits.append((producible, row))

            coverage_rows.append(row)

        if not limits:
            return {
                "materials": coverage_rows,
                "max_pa_producible_from_stock": None,
                "max_pa_producible_from_stock_exact": None,
                "limiting_raw_material_code": None,
                "limiting_raw_material_description": None,
            }

        limiting_producible, limiting_row = min(limits, key=lambda item: item[0])
        max_exact = max(0.0, limiting_producible)

        from app.domain.services.product.product_playbook_numeric_service import (
            ProductPlaybookNumericService,
        )

        return {
            "materials": coverage_rows,
            "max_pa_producible_from_stock": str(int(max_exact // 1)),
            "max_pa_producible_from_stock_exact": ProductPlaybookNumericService.format_quantity(
                max_exact
            ),
            "limiting_raw_material_code": limiting_row.get("raw_material_code"),
            "limiting_raw_material_description": limiting_row.get("raw_material_description"),
        }

    @classmethod
    @lru_cache(maxsize=1)
    def _bundle(cls) -> dict[str, Any]:
        with _CONTENT_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        return dict(payload) if isinstance(payload, dict) else {}
