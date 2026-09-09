"""PresentationDeterministicIntentBinder — heatmap partial completion invariants."""

from __future__ import annotations

from app.domain.entities.presentation_spec import PresentationIntent
from app.domain.services.presentation_data_profile_builder_service import (
    PresentationDataProfileBuilderService,
)
from app.domain.services.presentation_deterministic_intent_binder_service import (
    PresentationDeterministicIntentBinderService,
)

_STOCK_LIKE = [
    {"product_code": "P1", "branch": "01", "warehouse": "01", "current_quantity": 10.0},
    {"product_code": "P1", "branch": "01", "warehouse": "50", "current_quantity": 0.0},
    {"product_code": "P1", "branch": "02", "warehouse": "01", "current_quantity": 20.0},
    {"product_code": "P1", "branch": "02", "warehouse": "99", "current_quantity": 5.0},
]


def _profile(rows=None):
    return PresentationDataProfileBuilderService.build(rows or _STOCK_LIKE)


def test_positive_partial_deposito_completes_second_axis():
    profile = _profile()
    intent = PresentationIntent(
        view="chart",
        mark="heatmap",
        dimension_concepts=("depósito",),
        palette_family="sequential-blue",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert {spec.encoding["x"].field, spec.encoding["y"].field} <= set(
        profile.dimension_candidates
    )
    assert "warehouse" in {spec.encoding["x"].field, spec.encoding["y"].field}
    assert spec.encoding["color"].field == "current_quantity"


def test_sibling_explicit_filial_armazem():
    profile = _profile()
    intent = PresentationIntent(
        view="chart",
        mark="heatmap",
        dimension_concepts=("filial", "armazém"),
        palette_family="sequential-blue",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert spec.encoding["x"].field == "branch"
    assert spec.encoding["y"].field == "warehouse"


def test_sibling_slash_aliases_same_slot_then_complete():
    profile = _profile()
    intent = PresentationIntent(
        view="chart",
        mark="heatmap",
        dimension_concepts=("produto", "depósito/filial"),
        palette_family="sequential-blue",
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert len({spec.encoding["x"].field, spec.encoding["y"].field}) == 2


def test_negative_single_discriminant_does_not_invent_axis():
    rows = [{"region": "N", "qty": 1}, {"region": "S", "qty": 2}]
    profile = PresentationDataProfileBuilderService.build(rows)
    intent = PresentationIntent(view="chart", mark="heatmap", dimension_concepts=())
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is None


def test_negative_no_measure():
    rows = [
        {"branch": "01", "warehouse": "01", "label": "a"},
        {"branch": "02", "warehouse": "50", "label": "b"},
    ]
    profile = PresentationDataProfileBuilderService.build(rows)
    intent = PresentationIntent(
        view="chart",
        mark="heatmap",
        dimension_concepts=("filial", "armazém"),
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is None


def test_negative_bar_mark_does_not_use_heatmap_completion_pair():
    profile = _profile()
    intent = PresentationIntent(
        view="chart",
        mark="bar",
        dimension_concepts=("depósito",),
    )
    spec, _ = PresentationDeterministicIntentBinderService.bind(intent, profile)
    assert spec is not None
    assert spec.mark == "bar"
    assert "y" in spec.encoding
    assert "color" not in spec.encoding or spec.encoding.get("color") is None
