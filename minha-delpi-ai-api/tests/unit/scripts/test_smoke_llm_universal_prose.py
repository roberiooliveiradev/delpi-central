"""Smoke P5.6 — estrutura do script matriz Playbook 19."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "smoke_llm_universal_prose.py"
    )
    spec = importlib.util.spec_from_file_location("smoke_llm_universal_prose", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_smoke_scenarios_cover_playbook_19_matrix():
    module = _load_module()

    assert set(module.SCENARIOS) >= {
        "factory_status",
        "playbook_top_items",
        "kpi_cpv",
        "sql",
        "api_error",
    }

    for scenario_id, spec in module.SCENARIOS.items():
        assert str(spec.get("question") or "").strip(), scenario_id
        assert str(spec.get("pathHint") or "").strip(), scenario_id


def test_evaluate_structural_flags_missing_decoupling():
    module = _load_module()

    gaps = module._evaluate_structural(
        scenario="factory_status",
        mode="normal",
        tool_meta={
            "ok": True,
            "path": "/products/90269002/factory-status",
            "proseDeliveryMode": "template",
            "textPresentation": {"markdown": "### Template"},
            "humanizedSummary": {"linhas": ["- legado"]},
        },
        template_similarity=0.0,
        require_ok_tool=True,
    )

    assert gaps
    assert any("dataOnlyPresentation" in gap for gap in gaps)
    assert any("humanizedSummary" in gap for gap in gaps)
