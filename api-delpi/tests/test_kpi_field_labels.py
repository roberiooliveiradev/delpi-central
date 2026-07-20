from app.interface.http.kpi_field_labels import (
    COMMON_SCALAR_FIELD_LABELS,
    COMMERCIAL_ROL_FIELD_LABELS,
    FINANCIAL_EBITDA_FIELD_LABELS,
    FINANCIAL_ROL_FIELD_LABELS,
    HR_FIELD_LABELS,
    PRODUCTION_OEE_FIELD_LABELS,
    QUALITY_PPM_FIELD_LABELS,
    SI_GOAL_FIELD_LABELS,
    SUPPLIES_CPV_FIELD_LABELS,
    infer_scalar_field_formats,
    kpi_fields,
    merge_kpi_field_labels,
)


def test_kpi_fields_merges_common_si_and_route_bundles():
    fields = kpi_fields(FINANCIAL_ROL_FIELD_LABELS)

    assert fields["branch"] == "Filial"
    assert fields["goal_label"] == "Meta"
    assert fields["gross_revenue"] == "Receita bruta"
    assert fields["rol"] == "ROL"


def test_commercial_rol_target_fields_use_humanized_labels():
    fields = kpi_fields(COMMERCIAL_ROL_FIELD_LABELS)

    assert fields["rol"] == "ROL realizado"
    assert fields["target"] == "Meta ROL (R$)"
    assert fields["rol_target_pct"] == "Atingimento da meta ROL (%)"
    assert fields["branch"] == "Filial"


def test_department_kpi_bundles_contextualize_target_labels():
    assert kpi_fields(FINANCIAL_EBITDA_FIELD_LABELS)["target"] == "Meta EBITDA"
    assert kpi_fields(PRODUCTION_OEE_FIELD_LABELS)["target"] == "Meta OEE (%)"
    assert kpi_fields(QUALITY_PPM_FIELD_LABELS)["target"] == "Meta PPM"
    assert kpi_fields(HR_FIELD_LABELS)["goals_by_metric"] == "Metas por indicador"
    assert kpi_fields(SUPPLIES_CPV_FIELD_LABELS)["target"] == "Meta CPV"


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


def test_infer_scalar_field_formats_from_kpi_labels():
    fields = kpi_fields(FINANCIAL_ROL_FIELD_LABELS)
    formats = infer_scalar_field_formats(fields)

    assert formats["gross_revenue"] == "currency"
    assert formats["returns"] == "currency"
