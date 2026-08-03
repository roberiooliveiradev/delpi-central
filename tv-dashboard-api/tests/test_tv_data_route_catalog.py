from tv_app.application.services.comunicado_data_params_service import merge_data_params, param_inherited_from_slide
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
    """Hubs com enrich SI devem listar Meta no Campo dinâmico (não só via discovery)."""
    catalog = TvDataRouteCatalogService()
    route = catalog.get_route("get_lmps_dashboard_summary")
    assert route is not None
    assert "comparable_goal" in (route.get("valueFields") or [])
    labels = route.get("valueFieldLabels") or {}
    assert labels.get("comparable_goal") == "Meta"


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


def test_merge_data_params_todas_branch_clears_inherited():
    """Todas = consolidado — não encaminhar branch à api-delpi."""
    merged = merge_data_params(
        playlist_defaults=None,
        slide_filters=None,
        block_params={"branch": "01"},
        input_overrides={"branch": "Todas"},
    )
    assert "branch" not in merged


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
