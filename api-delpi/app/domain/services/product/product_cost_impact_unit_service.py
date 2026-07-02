"""Normalização de base de custo para simulador de impacto — PA em MI (milheiro)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.services.product.product_playbook_numeric_service import (
    ProductPlaybookNumericService,
)

_CONTENT_PATH = (
    Path(__file__).resolve().parents[3]
    / "content"
    / "product_cost_impact_units.json"
)


class ProductCostImpactUnitService:
    """Documenta e valida a base por 1 PA/MI do produto pai no simulador de custo."""

    @classmethod
    def resolve_parent_profile(cls, parent_unit: str | None) -> dict[str, Any]:
        normalized = str(parent_unit or "").strip().upper()
        bundle = cls._bundle()
        default = bundle.get("default") if isinstance(bundle.get("default"), dict) else {}
        parent_units = (
            bundle.get("parentUnits") if isinstance(bundle.get("parentUnits"), dict) else {}
        )
        profile = parent_units.get(normalized) if normalized else None

        if not isinstance(profile, dict):
            profile = {}

        catalog_pieces = float(
            profile.get("catalogPiecesPerUnit")
            or default.get("parentCatalogPiecesPerUnit")
            or 1
        )

        return {
            "catalog_unit": str(profile.get("catalogUnit") or normalized or "").strip() or None,
            "catalog_pieces_per_unit": catalog_pieces,
            "standard_cost_unit": str(
                profile.get("standardCostUnit") or profile.get("catalogUnit") or normalized or ""
            ).strip()
            or None,
            "material_cost_unit": str(
                profile.get("materialCostUnit") or profile.get("catalogUnit") or normalized or ""
            ).strip()
            or None,
        }

    @classmethod
    def build_extended_cost(
        cls,
        *,
        quantity_per_pa: object,
        unit_cost: object,
    ) -> float:
        quantity = ProductPlaybookNumericService.to_float(quantity_per_pa)
        cost = ProductPlaybookNumericService.to_float(unit_cost)
        return quantity * cost

    @classmethod
    def resolve_comparability(
        cls,
        *,
        total_material_cost: float,
        pa_standard_cost: float,
    ) -> dict[str, Any]:
        bundle = cls._bundle()
        config = bundle.get("comparability") if isinstance(bundle.get("comparability"), dict) else {}
        max_ratio = float(config.get("maxMaterialToPaRatio") or 5.0)
        min_ratio = float(config.get("minMaterialToPaRatio") or 0.05)

        if pa_standard_cost <= 0 or total_material_cost <= 0:
            return {
                "pa_cost_comparable": False,
                "material_to_pa_cost_ratio": None,
                "material_cost_vs_pa_standard_percent": None,
            }

        ratio = total_material_cost / pa_standard_cost
        comparable = min_ratio <= ratio <= max_ratio

        return {
            "pa_cost_comparable": comparable,
            "material_to_pa_cost_ratio": ratio,
            "material_cost_vs_pa_standard_percent": (ratio * 100.0) if comparable else None,
        }

    @classmethod
    def build_cost_basis(
        cls,
        *,
        parent_unit: str | None,
        pa_standard_cost: float,
        total_material_cost: float,
    ) -> dict[str, Any]:
        profile = cls.resolve_parent_profile(parent_unit)
        catalog_unit = profile.get("catalog_unit")
        pieces = float(profile.get("catalog_pieces_per_unit") or 1.0)
        standard_unit = profile.get("standard_cost_unit") or parent_unit
        material_unit = profile.get("material_cost_unit") or parent_unit

        basis: dict[str, Any] = {
            "reference_quantity": 1.0,
            "reference_unit": "PA",
            "standard_cost_unit": standard_unit,
            "material_cost_unit": material_unit,
            "pa_standard_cost_basis": f"1 {standard_unit or 'PA'}",
            "material_cost_basis": f"1 {material_unit or 'PA'}",
        }

        if catalog_unit:
            basis["catalog_unit"] = catalog_unit
            basis["catalog_pieces_per_unit"] = pieces
            basis["catalog_quantity_per_reference"] = 1.0

        if pa_standard_cost > 0 and pieces > 1:
            basis["pa_standard_cost_per_piece"] = pa_standard_cost / pieces

        if total_material_cost > 0 and pieces > 1:
            basis["total_material_cost_per_piece"] = total_material_cost / pieces

        return basis

    @classmethod
    @lru_cache(maxsize=1)
    def _bundle(cls) -> dict[str, Any]:
        with _CONTENT_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        return dict(payload) if isinstance(payload, dict) else {}
