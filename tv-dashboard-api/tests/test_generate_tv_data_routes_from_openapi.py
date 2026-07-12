"""Testes do gerador tv_data_routes.json × OpenAPI baseline v2."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "generate_tv_data_routes_from_openapi.py"
BASELINE = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"
ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
OVERLAYS_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_route_overlays.json"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_tv_data_routes_from_openapi", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_includes_all_get_operations():
    gen = _load_generator_module()
    openapi_ops = gen.load_openapi_get_operations(BASELINE)
    generated = gen.generate_routes(
        baseline_path=BASELINE,
        routes_path=ROUTES_PATH,
        overlays_path=OVERLAYS_PATH,
    )
    assert len(generated) == len(openapi_ops)
    assert len(generated) >= 200


def test_manual_enrichment_preserved_for_oee():
    gen = _load_generator_module()
    generated = gen.generate_routes(
        baseline_path=BASELINE,
        routes_path=ROUTES_PATH,
        overlays_path=OVERLAYS_PATH,
    )
    oee = next(item for item in generated if item["operationId"] == "get_overall_equipment_effectiveness_pct")
    assert oee["label"] == "OEE — visão geral"
    assert oee.get("valueFields")
    assert oee.get("paramSchema")


def test_openapi_parameters_become_param_schema_for_closing_rate():
    gen = _load_generator_module()
    schema, strategy = gen.build_param_schema_from_openapi(
        [
            {"name": "branch", "required": False, "type": "string"},
            {"name": "start_date", "required": False, "type": "string"},
            {"name": "end_date", "required": False, "type": "string"},
            {
                "name": "customer_segment",
                "required": False,
                "type": "string",
                "description": "Segmento",
            },
        ]
    )
    assert strategy == "date_range"
    assert "periodDays" in schema
    assert "branch" in schema
    assert "customer_segment" in schema
    assert "start_date" not in schema
    assert "end_date" not in schema

    generated = gen.generate_routes(
        baseline_path=BASELINE,
        routes_path=ROUTES_PATH,
        overlays_path=OVERLAYS_PATH,
    )
    closing = next(item for item in generated if item["operationId"] == "get_sales_conversion_rate")
    assert closing.get("paramStrategy") == "date_range"
    assert "periodDays" in (closing.get("paramSchema") or {})
    assert "customer_segment" in (closing.get("paramSchema") or {})
    assert closing.get("valueFields")


def test_catalog_has_majority_param_schemas_from_openapi():
    routes = json.loads(ROUTES_PATH.read_text(encoding="utf-8")).get("routes") or []
    with_schema = sum(1 for item in routes if item.get("paramSchema"))
    assert with_schema >= 100


def test_catalog_file_matches_generator_check():
    gen = _load_generator_module()
    generated = gen.generate_routes(
        baseline_path=BASELINE,
        routes_path=ROUTES_PATH,
        overlays_path=OVERLAYS_PATH,
    )
    stored = json.loads(ROUTES_PATH.read_text(encoding="utf-8")).get("routes") or []
    assert stored == generated


def test_overlays_file_exists_for_curated_routes():
    payload = json.loads(OVERLAYS_PATH.read_text(encoding="utf-8"))
    overlays = payload.get("overlays") or {}
    assert "get_overall_equipment_effectiveness_pct" in overlays
    assert "get_sales_conversion_rate" in overlays
