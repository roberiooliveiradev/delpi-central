"""Locale catalog — v2 bilíngue + compat v1 + params globais."""

from app.domain.services.route_locale_catalog_service import (
    apply_route_locale_to_x_delpi,
    load_global_param_locale,
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


def test_route_locale_department_indicators_bilingual():
    entry = route_locale_for_operation("get_dashboard_department_indicators")
    assert entry is not None
    assert entry["category"] == "system"
    assert "metas" in entry["locale"]["pt-BR"]["description"].lower() or "realizado" in entry["locale"]["pt-BR"]["description"].lower()
    all_entry = route_locale_for_operation("get_dashboard_departments_indicators")
    assert all_entry is not None
    assert all_entry["locale"]["pt-BR"]["label"]


def test_tv_audience_compat_from_pt_br():
    tv = tv_audience_for_operation("get_overall_equipment_effectiveness_pct")
    assert tv is not None
    assert "whenToUse" in tv


def test_global_param_locale_catalog():
    params = load_global_param_locale()
    assert params["branch"]["locale"]["en"]["label"] == "Branch"
    assert params["branch"]["locale"]["pt-BR"]["label"] == "Filial"
    assert params["customer_codes"]["locale"]["pt-BR"]["label"] == "Códigos de clientes"
    assert params["include"]["locale"]["pt-BR"]["label"] == "Seções opcionais"


def test_global_param_enum_labels_bilingual():
    params = load_global_param_locale()
    rank = params["rank_by"]["enumLabels"]["stop_reason"]
    assert rank["en"]["label"] == "Stop reason"
    assert rank["pt-BR"]["label"] == "Motivo de parada"
    metric = params["metric"]["enumLabels"]
    assert metric["hours"]["en"]["label"] == "Hours"
    assert metric["hours"]["pt-BR"]["label"] == "Horas"
    # Todo valor de enum label exige EN e pt-BR.
    for param, entry in params.items():
        enums = entry.get("enumLabels")
        if not isinstance(enums, dict):
            continue
        for code, langs in enums.items():
            assert langs.get("en", {}).get("label"), f"{param}.{code}.en"
            assert langs.get("pt-BR", {}).get("label"), f"{param}.{code}.pt-BR"


def test_apply_route_locale_to_x_delpi_merges():
    base = {
        "entity": "dashboard_department_idd",
        "shape": "scalar",
        "presentation": {"strategy": "as_delivered"},
    }
    merged = apply_route_locale_to_x_delpi(
        base,
        "get_dashboard_department_idd",
        param_names={"department_id", "branch"},
    )
    assert merged["locale"]["en"]["summary"]
    assert merged["tv"]["whenToUse"]
    # Params globais entram só quando listados em param_names.
    assert merged["params"]["branch"]["locale"]["pt-BR"]["label"] == "Filial"
    # Route-specific sobrescreve / complementa.
    assert merged["params"]["department_id"]["locale"]["pt-BR"]["label"] == "Departamento"
    # enumLabels bilíngues sobem no x-delpi.params.
    dept = merged["params"]["department_id"]["enumLabels"]["production"]
    assert dept["en"]["label"] == "Production"
    assert dept["pt-BR"]["label"] == "Produção"


def test_apply_route_locale_filters_global_params_to_route():
    base = {"entity": "x", "shape": "scalar", "presentation": {"strategy": "as_delivered"}}
    merged = apply_route_locale_to_x_delpi(
        base,
        "get_dashboard_department_idd",
        param_names={"department_id"},
    )
    assert "department_id" in merged["params"]
    assert "branch" not in merged.get("params", {})


def test_financial_rol_vs_by_branch_when_not_to_use():
    financial = route_locale_for_operation("get_financial_rol")
    by_branch = route_locale_for_operation("get_commercial_rol_by_branch")
    assert financial is not None
    assert by_branch is not None
    assert "whenNotToUse" in financial["locale"]["en"]
    assert "whenNotToUse" in by_branch["locale"]["en"]
    assert "/financial/rol" in by_branch["locale"]["en"]["whenNotToUse"]
    assert "by-branch" in financial["locale"]["en"]["whenNotToUse"]
    merged = apply_route_locale_to_x_delpi({}, "get_commercial_rol_by_branch")
    assert "whenNotToUse" in merged["locale"]["pt-BR"]


def test_product_factory_status_locale_disambiguates_pcp():
    factory = route_locale_for_operation("get_product_factory_status")
    assert factory is not None
    assert "status fabril" in factory["locale"]["pt-BR"]["whenToUse"].lower()
    assert "pcp-orders" in factory["locale"]["en"]["whenNotToUse"]


def test_audience_catalog_has_no_root_level_route_orphans():
    """Regressão: entries fora de routes{} nunca entram no OpenAPI."""
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "app/content/tv_route_audience.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    reserved = {"version", "description", "routes"}
    orphans = [key for key in payload if key not in reserved]
    assert orphans == [], f"route orphans at root: {orphans}"
    assert "get_commercial_rol_by_branch" in payload["routes"]
