from app.interface.http.kpi_field_labels import (
    COMMON_SCALAR_FIELD_LABELS,
    FINANCIAL_ROL_FIELD_LABELS,
    HR_FIELD_LABELS,
    SI_GOAL_FIELD_LABELS,
    kpi_fields,
    merge_kpi_field_labels,
)


def test_kpi_fields_merges_common_si_and_route_bundles():
    fields = kpi_fields(FINANCIAL_ROL_FIELD_LABELS)

    assert fields["branch"] == "Filial"
    assert fields["goal_label"] == "Meta"
    assert fields["gross_revenue"] == "Receita bruta"
    assert fields["rol"] == "ROL"


def test_merge_kpi_field_labels_later_bundle_overrides():
    merged = merge_kpi_field_labels(
        {"value": "Valor A"},
        {"value": "Valor B"},
    )

    assert merged["value"] == "Valor B"


def test_hr_bundle_contains_portal_rh_indicators():
    fields = kpi_fields(HR_FIELD_LABELS)

    assert fields["turnover_pct"] == "Turnover (%)"
    assert fields["active_pdi_count"] == "PDIs ativos"
    assert "branch" in COMMON_SCALAR_FIELD_LABELS
    assert "has_goal" in SI_GOAL_FIELD_LABELS
