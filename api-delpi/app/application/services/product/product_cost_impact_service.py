from app.application.dto.product.product_cost_impact_request import PriceSource


def _to_float(value) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def resolve_unit_cost(
    *,
    standard_cost,
    last_purchase_price,
    price_source: PriceSource,
) -> float:
    standard = _to_float(standard_cost)
    last_purchase = _to_float(last_purchase_price)

    if price_source == "last_purchase":
        return last_purchase if last_purchase > 0 else standard

    return standard if standard > 0 else last_purchase


def build_cost_impact_simulation(
    *,
    product: dict | None,
    items: list[dict],
    price_source: PriceSource,
    adjustment_percent: float,
    top_n: int | None,
) -> dict:
    from app.domain.services.product.product_cost_impact_unit_service import (
        ProductCostImpactUnitService,
    )
    from app.domain.services.product.product_pa_bom_reference_service import (
        ProductPaBomReferenceService,
    )

    if not product:
        return {
            "product": None,
            "price_source": price_source,
            "adjustment_percent": adjustment_percent,
            "materials": {"items": [], "total": 0, "returned": 0},
            "summary": {
                "total_raw_materials": 0,
                "total_material_cost": 0.0,
                "simulated_total_material_cost": 0.0,
                "projected_cost_delta": 0.0,
            },
            "simulation": {
                "adjustment_percent": adjustment_percent,
                "projected_total_material_cost": 0.0,
                "projected_cost_delta": 0.0,
            },
        }

    pa_standard_cost = _to_float(product.get("standard_cost"))
    multiplier = 1 + (adjustment_percent / 100.0)
    product_unit = str(product.get("unit") or "").strip() or None

    enriched: list[dict] = []
    for item in items:
        quantity_per_pa = ProductPaBomReferenceService.quantity_required_for_one_pa(
            item.get("quantity_per_pa"),
            product_unit,
        )
        unit_cost = resolve_unit_cost(
            standard_cost=item.get("standard_cost"),
            last_purchase_price=item.get("last_purchase_price"),
            price_source=price_source,
        )
        simulated_unit_cost = unit_cost * multiplier
        extended_cost = ProductCostImpactUnitService.build_extended_cost(
            quantity_per_pa=quantity_per_pa,
            unit_cost=unit_cost,
        )
        simulated_extended_cost = ProductCostImpactUnitService.build_extended_cost(
            quantity_per_pa=quantity_per_pa,
            unit_cost=simulated_unit_cost,
        )

        enriched.append(
            {
                **item,
                "quantity_per_pa": quantity_per_pa,
                "unit_cost": unit_cost,
                "extended_cost": extended_cost,
                "simulated_unit_cost": simulated_unit_cost,
                "simulated_extended_cost": simulated_extended_cost,
                "cost_delta": simulated_extended_cost - extended_cost,
            }
        )

    total_material_cost = sum(row["extended_cost"] for row in enriched)
    simulated_total = sum(row["simulated_extended_cost"] for row in enriched)
    projected_delta = simulated_total - total_material_cost

    comparability = ProductCostImpactUnitService.resolve_comparability(
        total_material_cost=total_material_cost,
        pa_standard_cost=pa_standard_cost,
    )
    pa_cost_comparable = bool(comparability.get("pa_cost_comparable"))
    material_to_pa_ratio = comparability.get("material_to_pa_cost_ratio")

    ranked = sorted(enriched, key=lambda row: row["extended_cost"], reverse=True)
    materials: list[dict] = []

    for index, row in enumerate(ranked, start=1):
        impact_on_material_cost = (
            (row["extended_cost"] / total_material_cost) * 100
            if total_material_cost > 0
            else 0.0
        )
        impact_on_pa_cost = (
            (row["extended_cost"] / pa_standard_cost) * 100
            if pa_cost_comparable
            else None
        )
        simulated_impact_on_pa_cost = (
            (row["simulated_extended_cost"] / pa_standard_cost) * 100
            if pa_cost_comparable
            else None
        )

        materials.append(
            {
                "rank": index,
                "raw_material_code": row.get("raw_material_code"),
                "raw_material_description": row.get("raw_material_description"),
                "unit": row.get("unit"),
                "group_code": row.get("group_code"),
                "quantity_per_pa": row["quantity_per_pa"],
                "unit_cost": row["unit_cost"],
                "extended_cost": row["extended_cost"],
                "impact_on_material_cost_percent": impact_on_material_cost,
                "impact_on_pa_cost_percent": impact_on_pa_cost,
                "simulated_unit_cost": row["simulated_unit_cost"],
                "simulated_extended_cost": row["simulated_extended_cost"],
                "simulated_impact_on_pa_cost_percent": simulated_impact_on_pa_cost,
                "cost_delta": row["cost_delta"],
                "path": row.get("path"),
            }
        )

    if top_n is not None and top_n > 0:
        materials = materials[:top_n]

    top_share = materials[0]["impact_on_material_cost_percent"] if materials else 0.0

    cost_basis = ProductCostImpactUnitService.build_cost_basis(
        parent_unit=product_unit,
        pa_standard_cost=pa_standard_cost,
        total_material_cost=total_material_cost,
    )

    summary = {
        "total_raw_materials": len(enriched),
        "returned_materials": len(materials),
        "total_material_cost": total_material_cost,
        "simulated_total_material_cost": simulated_total,
        "projected_cost_delta": projected_delta,
        "top_material_impact_percent": top_share,
        "pa_standard_cost": pa_standard_cost,
        "material_to_pa_cost_ratio": material_to_pa_ratio,
        "material_cost_vs_pa_standard_percent": comparability.get(
            "material_cost_vs_pa_standard_percent"
        ),
        "simulated_material_cost_vs_pa_standard_percent": (
            (simulated_total / pa_standard_cost) * 100
            if pa_cost_comparable
            else None
        ),
        "pa_cost_comparable": pa_cost_comparable,
        "cost_basis": cost_basis,
    }

    reference = ProductPaBomReferenceService.resolve_from_product(product)
    enriched_product = dict(product)
    enriched_product["pa_reference"] = reference.as_dict()

    return {
        "product": enriched_product,
        "pa_reference": reference.as_dict(),
        "cost_basis": cost_basis,
        "price_source": price_source,
        "adjustment_percent": adjustment_percent,
        "materials": {
            "items": materials,
            "total": len(enriched),
            "returned": len(materials),
        },
        "summary": summary,
        "simulation": {
            "adjustment_percent": adjustment_percent,
            "projected_total_material_cost": simulated_total,
            "projected_cost_delta": projected_delta,
            "projected_pa_cost_delta_percent": (
                (projected_delta / pa_standard_cost) * 100
                if pa_cost_comparable
                else None
            ),
            "material_to_pa_cost_ratio": material_to_pa_ratio,
        },
    }
