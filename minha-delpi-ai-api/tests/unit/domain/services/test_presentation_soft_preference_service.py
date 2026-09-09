"""Unit: soft preferences do not override hard Spec bindings."""

from app.domain.entities.presentation_data_profile import (
    PresentationDataProfile,
    PresentationFieldProfile,
)
from app.domain.entities.presentation_spec import EncodingChannel, PresentationSpec
from app.domain.services.presentation_soft_preference_service import (
    PresentationSoftPreferenceService,
)


def test_heatmap_gets_sequential_blue_when_missing_palette():
    """Positive: soft completa palette heatmap."""
    spec = PresentationSpec(view="chart", mark="heatmap", legend_visible=None)
    applied = PresentationSoftPreferenceService.apply(spec)
    assert applied is not None
    assert applied.palette_family == "sequential-blue"
    assert applied.legend_visible is False
    assert PresentationSoftPreferenceService.score(applied) > 0


def test_soft_does_not_override_explicit_palette():
    """Sibling: hard palette preservada."""
    spec = PresentationSpec(
        view="chart",
        mark="bar",
        encoding={
            "x": EncodingChannel(field="branch"),
            "y": EncodingChannel(field="balance"),
        },
        palette_family="warm",
        legend_visible=True,
    )
    applied = PresentationSoftPreferenceService.apply(spec)
    assert applied is not None
    assert applied.palette_family == "warm"
    assert applied.legend_visible is True


def test_soft_does_not_invent_mark_against_table_view():
    """Negative: soft não troca view table por chart."""
    fields = tuple(
        PresentationFieldProfile(
            key=f"c{i}",
            primitive_type="string",
            semantic_type="nominal",
            cardinality=3,
            cardinality_band="low",
            null_rate=0.0,
            is_constant=False,
            is_dimension_candidate=True,
            is_measure_candidate=False,
        )
        for i in range(12)
    )
    profile = PresentationDataProfile(
        row_count=12,
        sampled_row_count=12,
        fields=fields,
    )
    spec = PresentationSpec(
        view="table",
        fields=tuple(f"c{i}" for i in range(12)),
        provenance="DETERMINISTIC",
    )
    applied = PresentationSoftPreferenceService.apply(spec, profile=profile)
    assert applied is not None
    assert applied.view == "table"
    assert applied.mark is None
    assert len(applied.fields) <= 8
