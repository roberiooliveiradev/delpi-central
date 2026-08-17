from tv_app.application.services.comunicado_data_params_service import (
    merge_data_params,
    param_inherited_from_slide,
    project_branch_params_onto_route_schema,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_catalog_lists_allowlist_routes():
    catalog = TvDataRouteCatalogService()
    routes = catalog.list_routes()
    assert len(routes) >= 200
    ids = {item["operationId"] for item in routes}
    assert "get_overall_equipment_effectiveness_pct" in ids
    assert "get_production_oee_series" in ids
    assert "get_production_otd_series" in ids
    assert "get_ppm_external_summary" in ids
    assert "get_supplies_stock_value" in ids
    assert "get_dashboard_department_idd" in ids
    assert "get_dashboard_department_idd_dashboard_department_idd_get" not in ids


def test_catalog_resolves_legacy_department_idd_operation_id():
    """Playlists salvas com operationId auto-FastAPI devem resolver no canônico."""
    from tv_app.application.services.tv_data_route_catalog_service import (
        normalize_data_binding_operation_id,
        resolve_canonical_operation_id,
    )

    legacy = "get_dashboard_department_idd_dashboard_department_idd_get"
    canonical = "get_dashboard_department_idd"
    assert resolve_canonical_operation_id(legacy) == canonical

    catalog = TvDataRouteCatalogService()
    route = catalog.get_route(legacy)
    assert route is not None
    assert route["operationId"] == canonical
    assert catalog.is_allowed(legacy)
    assert route["paramSchema"]["department_id"]["enum"]

    binding = normalize_data_binding_operation_id({"operationId": legacy, "params": {"department_id": "commercial"}})
    assert binding is not None
    assert binding["operationId"] == canonical


def test_catalog_lmp_summary_exposes_meta_for_si_goal_picker():
    """Hubs com enrich SI devem listar a tríade de meta no Campo dinâmico."""
    catalog = TvDataRouteCatalogService()
    route = catalog.get_route("get_lmps_dashboard_summary")
    assert route is not None
    fields = route.get("valueFields") or []
    assert "comparable_goal" in fields
    assert "goal_value" in fields
    assert "reference_goal" in fields
    labels = route.get("valueFieldLabels") or {}
    assert labels.get("comparable_goal") == "Meta do período"
    assert labels.get("goal_value") == "Meta cadastrada"
    assert labels.get("reference_goal") == "Meta mês (referência)"


def test_catalog_all_exposes_si_goal_hubs_have_triad_labels():
    import json
    from pathlib import Path

    from tests.fixtures.si_goal_contract_cases import SI_GOAL_FIELD_LABELS_PT

    overlays_path = (
        Path(__file__).resolve().parents[1]
        / "tv_app"
        / "content"
        / "tv_data_route_overlays.json"
    )
    doc = json.loads(overlays_path.read_text(encoding="utf-8"))
    hub_ids = [
        key
        for key, overlay in (doc.get("overlays") or {}).items()
        if isinstance(overlay, dict) and overlay.get("exposesSiGoal")
    ]
    assert hub_ids, "expected at least one exposesSiGoal hub"
    catalog = TvDataRouteCatalogService()
    for operation_id in hub_ids:
        route = catalog.get_route(operation_id)
        assert route is not None, operation_id
        fields = route.get("valueFields") or []
        labels = route.get("valueFieldLabels") or {}
        for key, label in SI_GOAL_FIELD_LABELS_PT.items():
            assert key in fields, (operation_id, key)
            assert labels.get(key) == label, (operation_id, key, labels.get(key))


def test_catalog_si_meta_routes_list_value_field():
    from tests.fixtures.si_goal_contract_cases import SI_META_OPERATION_IDS_SAMPLE

    catalog = TvDataRouteCatalogService()
    for operation_id in SI_META_OPERATION_IDS_SAMPLE:
        route = catalog.get_route(operation_id)
        assert route is not None, operation_id
        fields = route.get("valueFields") or []
        assert "value" in fields, operation_id


def test_merge_data_params_slide_overrides_playlist_block_overrides_slide():
    merged = merge_data_params(
        playlist_defaults={"branch": "01", "periodDays": 30},
        slide_filters={"branch": "02", "periodDays": 14},
        block_params={"periodDays": 7},
    )
    assert merged["branch"] == "02"
    assert merged["periodDays"] == 7


def test_merge_data_params_relative_preset_clears_stale_dates():
    """Slide this_month não herda start_date=0026 da programação."""
    merged = merge_data_params(
        playlist_defaults={
            "dateRangePreset": "custom",
            "start_date": "0026-07-01",
            "end_date": "2026-07-31",
        },
        slide_filters={"dateRangePreset": "this_month"},
        block_params=None,
    )
    assert merged["dateRangePreset"] == "this_month"
    assert "start_date" not in merged
    assert "end_date" not in merged


def test_merge_data_params_block_custom_without_dates_clears_inherited_dates():
    """Bloco custom vazio não reaproveita datas corruptas (causa do 400 24 meses)."""
    merged = merge_data_params(
        playlist_defaults={
            "dateRangePreset": "custom",
            "start_date": "0026-07-01",
            "end_date": "2026-07-31",
            "branch": "01",
        },
        slide_filters={"dateRangePreset": "this_month"},
        block_params={"dateRangePreset": "custom"},
    )
    assert merged["dateRangePreset"] == "custom"
    assert merged["branch"] == "01"
    assert "start_date" not in merged
    assert "end_date" not in merged


def test_merge_data_params_input_overrides_block_and_clears_preset():
    """Filtro interativo vence dateRangePreset/this_month da fonte."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"dateRangePreset": "this_month", "branch": "01"},
        input_overrides={"periodDays": 4},
    )
    assert merged["periodDays"] == 4
    assert merged["branch"] == "01"
    assert "dateRangePreset" not in merged


def test_merge_data_params_input_end_date_clears_preset_and_period_days():
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"dateRangePreset": "this_month", "periodDays": 30},
        input_overrides={"end_date": "2026-07-10"},
    )
    assert merged["end_date"] == "2026-07-10"
    assert "dateRangePreset" not in merged
    assert "periodDays" not in merged


def test_merge_data_params_previous_month_clears_inherited_competence():
    """Runtime «Mês passado» não pode deixar competence da fonte vencer o preset."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters={"department_id": "quality"},
        block_params={
            "department_id": "quality",
            "competence": "2026-08",
            "branch": "01",
        },
        input_overrides={
            "dateRangePreset": "previous_month",
            "branch": "01",
        },
    )
    assert merged["dateRangePreset"] == "previous_month"
    assert merged["branch"] == "01"
    assert merged["department_id"] == "quality"
    assert "competence" not in merged
    assert "start_date" not in merged
    assert "end_date" not in merged


def test_merge_data_params_custom_keeps_competence():
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"competence": "2026-07", "dateRangePreset": "custom"},
        input_overrides=None,
    )
    assert merged["competence"] == "2026-07"
    assert merged["dateRangePreset"] == "custom"


def test_merge_data_params_empty_branch_input_clears_inherited():
    """Input Filial vazio remove branch=01 da fonte (LMP consolidado)."""
    merged = merge_data_params(
        playlist_defaults={"branch": "01"},
        slide_filters=None,
        block_params={"branch": "01", "dateRangePreset": "this_month"},
        input_overrides={"branch": ""},
    )
    assert "branch" not in merged
    assert merged["dateRangePreset"] == "this_month"


def test_merge_data_params_all_branch_overrides_inherited():
    """all = consolidado canônico — grava wire `all` e remove herança 01/02."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"branch": "01"},
        input_overrides={"branch": "all"},
    )
    assert merged["branch"] == "all"

    merged_pt = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"branch": "01"},
        input_overrides={"branch": "Todas"},
    )
    assert merged_pt["branch"] == "all"


def test_param_inherited_from_slide():
    assert param_inherited_from_slide(
        "branch",
        slide_filters={"branch": "01"},
        block_params={},
    )
    assert not param_inherited_from_slide(
        "branch",
        slide_filters={"branch": "01"},
        block_params={"branch": "02"},
    )


def test_project_branch_params_playlist_branch_onto_refugo_filial():
    projected = project_branch_params_onto_route_schema(
        {"branch": "01", "dateRangePreset": "today"},
        {"filial": {"type": "string", "optional": True}},
    )
    assert projected.get("filial") == "01"
    assert "branch" not in projected
    assert projected.get("dateRangePreset") == "today"


def test_project_branch_params_filial_onto_branch_schema():
    projected = project_branch_params_onto_route_schema(
        {"filial": "02"},
        {"branch": {"type": "string", "optional": True}},
    )
    assert projected.get("branch") == "02"
    assert "filial" not in projected
