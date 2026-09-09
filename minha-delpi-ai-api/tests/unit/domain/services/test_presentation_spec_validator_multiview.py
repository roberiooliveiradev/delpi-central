"""Adversarial / multi-view caps for PresentationSpecValidatorService."""

from app.domain.entities.presentation_data_profile import (
    PresentationDataProfile,
    PresentationFieldProfile,
)
from app.domain.entities.presentation_spec import (
    PresentationDashboardPanelSpec,
    PresentationDashboardSpec,
    PresentationKpiSpec,
    PresentationSpec,
    PresentationTableSpec,
    PresentationTextSpec,
)
from app.domain.services.presentation_spec_validator_service import (
    PresentationSpecValidatorService,
)


def _profile(*keys: str) -> PresentationDataProfile:
    fields = tuple(
        PresentationFieldProfile(
            key=key,
            primitive_type="string",
            semantic_type="nominal",
            cardinality=3,
            cardinality_band="low",
            null_rate=0.0,
            is_constant=False,
            is_measure_candidate=key.endswith("_qty") or key == "balance",
            is_dimension_candidate=not (
                key.endswith("_qty") or key == "balance"
            ),
        )
        for key in keys
    )
    return PresentationDataProfile(
        row_count=len(keys) or 1,
        sampled_row_count=len(keys) or 1,
        fields=fields,
        dimension_candidates=tuple(
            item.key for item in fields if item.is_dimension_candidate
        ),
        measure_candidates=tuple(
            item.key for item in fields if item.is_measure_candidate
        ),
    )


def test_rejects_hex_in_label():
    """Positive adversarial: hex no Spec falha."""
    profile = _profile("product_code", "balance")
    result = PresentationSpecValidatorService.validate(
        PresentationSpec(
            view="table",
            fields=("product_code",),
            labels={"product_code": "Produto #089bdb"},
        ),
        profile=profile,
    )
    assert result.ok is False
    assert any(error.startswith("forbidden_style:") for error in result.errors)


def test_rejects_too_many_fields_and_kpi_cards():
    """Sibling: caps fields/KPI."""
    keys = tuple(f"col_{index}" for index in range(40))
    profile = _profile(*keys)
    too_many_fields = PresentationSpecValidatorService.validate(
        PresentationSpec(view="table", fields=keys),
        profile=profile,
    )
    assert too_many_fields.ok is False
    assert any(error.startswith("cap.fields:") for error in too_many_fields.errors)

    measure_keys = tuple(f"m_{index}" for index in range(12))
    kpi_profile = _profile(*measure_keys)
    too_many_cards = PresentationSpecValidatorService.validate(
        PresentationSpec(
            view="kpi",
            kpi=PresentationKpiSpec(measure_fields=measure_keys),
        ),
        profile=kpi_profile,
    )
    assert too_many_cards.ok is False
    assert any("cap.kpi.measureFields:" in error for error in too_many_cards.errors)


def test_rejects_invalid_dashboard_panel_and_section_plan():
    """Negative: panel presentation / sectionPlan fora da allowlist."""
    profile = _profile("product_code", "balance")
    bad_panel = PresentationSpecValidatorService.validate(
        PresentationSpec(
            view="dashboard",
            dashboard=PresentationDashboardSpec(
                panels=(
                    PresentationDashboardPanelSpec(
                        id="p1",
                        presentation="canvas",
                    ),
                )
            ),
        ),
        profile=profile,
    )
    assert bad_panel.ok is False
    assert any("unsupported_presentation" in error for error in bad_panel.errors)

    bad_text = PresentationSpecValidatorService.validate(
        PresentationSpec(
            view="text",
            text=PresentationTextSpec(section_plan=("summary", "inject_css")),
        ),
        profile=profile,
    )
    assert bad_text.ok is False
    assert any("unsupported_sectionPlan" in error for error in bad_text.errors)


def test_accepts_valid_nested_dashboard_and_cleans_unknown_hidden():
    """Positive: nested válido passa; hidden desconhecido é limpo."""
    profile = _profile("product_code", "balance", "branch")
    result = PresentationSpecValidatorService.validate(
        PresentationSpec(
            view="dashboard",
            dashboard=PresentationDashboardSpec(
                panels=(
                    PresentationDashboardPanelSpec(
                        id="kpi-top",
                        presentation="kpi",
                        measures=("balance",),
                    ),
                    PresentationDashboardPanelSpec(
                        id="table-main",
                        presentation="table",
                        fields=("product_code", "branch"),
                    ),
                )
            ),
            table=PresentationTableSpec(
                density="compact",
                hidden_fields=("ghost_col", "branch"),
            ),
            kpi=PresentationKpiSpec(measure_fields=("balance",)),
        ),
        profile=profile,
    )
    assert result.ok is True
    assert result.spec is not None
    assert result.spec.dashboard is not None
    assert len(result.spec.dashboard.panels) == 2
    assert result.spec.table is not None
    assert result.spec.table.hidden_fields == ("branch",)
