"""Testes do gerador tv_data_routes.json × OpenAPI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "generate_tv_data_routes_from_openapi.py"
BASELINE = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"
ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"


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
    generated = gen.generate_routes(baseline_path=BASELINE, routes_path=ROUTES_PATH)
    assert len(generated) == len(openapi_ops)
    assert len(generated) >= 200


def test_manual_enrichment_preserved_for_oee():
    gen = _load_generator_module()
    generated = gen.generate_routes(baseline_path=BASELINE, routes_path=ROUTES_PATH)
    oee = next(item for item in generated if item["operationId"] == "get_overall_equipment_effectiveness_pct")
    assert oee["label"] == "OEE — visão geral"
    assert oee.get("valueFields")
    assert oee.get("paramSchema")


def test_catalog_file_matches_generator_check():
    gen = _load_generator_module()
    generated = gen.generate_routes(baseline_path=BASELINE, routes_path=ROUTES_PATH)
    stored = json.loads(ROUTES_PATH.read_text(encoding="utf-8")).get("routes") or []
    assert stored == generated
