from app.domain.services.product.product_cost_impact_unit_service import (
    ProductCostImpactUnitService,
)


def test_resolve_parent_profile_for_mi_documents_milheiro_base() -> None:
    profile = ProductCostImpactUnitService.resolve_parent_profile("MI")

    assert profile["catalog_unit"] == "MI"
    assert profile["catalog_pieces_per_unit"] == 1000
    assert profile["standard_cost_unit"] == "MI"
    assert profile["material_cost_unit"] == "MI"


def test_build_cost_basis_exposes_per_piece_values_for_mi_parent() -> None:
    basis = ProductCostImpactUnitService.build_cost_basis(
        parent_unit="MI",
        pa_standard_cost=765.998,
        total_material_cost=49598.3456,
    )

    assert basis["pa_standard_cost_basis"] == "1 MI"
    assert basis["material_cost_basis"] == "1 MI"
    assert basis["catalog_pieces_per_unit"] == 1000
    assert basis["pa_standard_cost_per_piece"] == 765.998 / 1000
    assert basis["total_material_cost_per_piece"] == 49598.3456 / 1000


def test_resolve_comparability_marks_outlier_ratios_as_not_comparable() -> None:
    result = ProductCostImpactUnitService.resolve_comparability(
        total_material_cost=49598.3456,
        pa_standard_cost=765.998,
    )

    assert result["pa_cost_comparable"] is False
    assert result["material_to_pa_cost_ratio"] == 49598.3456 / 765.998
    assert result["material_cost_vs_pa_standard_percent"] is None


def test_resolve_comparability_keeps_ratio_for_balanced_products() -> None:
    total_material_cost = 449.57
    pa_standard_cost = 1550.19716

    result = ProductCostImpactUnitService.resolve_comparability(
        total_material_cost=total_material_cost,
        pa_standard_cost=pa_standard_cost,
    )

    assert result["pa_cost_comparable"] is True
    assert result["material_cost_vs_pa_standard_percent"] == (
        (total_material_cost / pa_standard_cost) * 100.0
    )
