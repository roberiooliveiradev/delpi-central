"""Locale catalog — v2 bilíngue + compat v1."""

from app.domain.services.route_locale_catalog_service import (
    apply_route_locale_to_x_delpi,
    route_locale_for_operation,
    tv_audience_for_operation,
)


def test_route_locale_department_idd_bilingual():
    entry = route_locale_for_operation("get_dashboard_department_idd")
    assert entry is not None
    assert entry["category"] == "system"
    assert entry["locale"]["en"]["summary"]
    assert entry["locale"]["pt-BR"]["whenToUse"]
    assert entry["params"]["department_id"]["locale"]["pt-BR"]["label"] == "Departamento"


def test_tv_audience_compat_from_pt_br():
    tv = tv_audience_for_operation("get_overall_equipment_effectiveness_pct")
    assert tv is not None
    assert "whenToUse" in tv


def test_apply_route_locale_to_x_delpi_merges():
    base = {
        "entity": "dashboard_department_idd",
        "shape": "scalar",
        "presentation": {"strategy": "as_delivered"},
    }
    merged = apply_route_locale_to_x_delpi(base, "get_dashboard_department_idd")
    assert merged["locale"]["en"]["summary"]
    assert merged["tv"]["whenToUse"]
