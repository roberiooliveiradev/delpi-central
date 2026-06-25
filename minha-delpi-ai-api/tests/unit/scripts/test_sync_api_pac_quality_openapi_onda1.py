"""Gate Onda 1 — OpenAPI api-pac antes do sync GPT."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_sync_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "sync_api_pac_quality_openapi.py"
    spec = importlib.util.spec_from_file_location("sync_api_pac_quality_openapi", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_validate_onda1_detects_missing_8d_and_evidences():
    sync = _load_sync_module()
    schema = {
        "paths": {
            "/quality/action-plans": {},
            "/quality/action-plans/intelligence/similar-cases": {},
            "/quality/action-plans/{plan_id}": {},
        }
    }
    missing = sync._validate_onda1_openapi_paths(schema)
    assert "/quality/action-plans/{plan_id}/rnc-8d" in missing
    assert "/quality/action-plans/{plan_id}/evidences" in missing


def test_validate_onda1_passes_when_all_required_paths_present():
    sync = _load_sync_module()
    schema = {"paths": {path: {} for path in sync.ONDA1_REQUIRED_OPENAPI_PATHS}}
    assert sync._validate_onda1_openapi_paths(schema) == []
