"""Unit tests — PresentationDataProfileBuilder."""

from __future__ import annotations

from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)


def test_profile_marks_unit_as_constant_not_dimension():
    rows = [
        {"product_code": "A", "warehouse": "W1", "unit": "UN", "planned_qty": 10},
        {"product_code": "B", "warehouse": "W2", "unit": "UN", "planned_qty": 20},
        {"product_code": "A", "warehouse": "W2", "unit": "UN", "planned_qty": 5},
    ]
    profile = PresentationDataProfileBuilderService.build(
        rows,
        label_bundle={
            "labels": {
                "product_code": "Código do produto",
                "warehouse": "Depósito",
                "planned_qty": "Qtd. planejada",
                "unit": "Unidade",
            },
            "formats": {"planned_qty": "quantity"},
            "sourceByKey": {"planned_qty": "catalog"},
        },
    )

    field_map = profile.field_map()
    assert field_map["unit"].is_constant is True
    assert field_map["unit"].is_dimension_candidate is False
    assert "unit" not in profile.dimension_candidates
    assert "product_code" in profile.dimension_candidates
    assert "warehouse" in profile.dimension_candidates
    assert "planned_qty" in profile.measure_candidates
    assert field_map["planned_qty"].display_label == "Qtd. planejada"
    assert field_map["planned_qty"].label_source == "CANONICAL_VOCABULARY"


def test_profile_marks_sensitive_email():
    rows = [{"email": "a@b.com", "score": 1}, {"email": "c@d.com", "score": 2}]
    profile = PresentationDataProfileBuilderService.build(rows)
    assert profile.field_map()["email"].sensitive is True
    assert profile.field_map()["email"].is_dimension_candidate is False


def test_sibling_measure_candidates_include_produced_qty():
    rows = [
        {"machine": "M1", "planned_qty": 10, "produced_qty": 8},
        {"machine": "M2", "planned_qty": 12, "produced_qty": 11},
    ]
    profile = PresentationDataProfileBuilderService.build(rows)
    assert "produced_qty" in profile.measure_candidates
    assert "planned_qty" in profile.measure_candidates
