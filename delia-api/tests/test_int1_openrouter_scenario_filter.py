"""Harness-only: DELIA_EVAL_SCENARIO_IDS filters instrumented eval scenarios."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_eval_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "int1_openrouter_qwen14b_instrumented_eval.py"
    )
    spec = importlib.util.spec_from_file_location(
        "int1_openrouter_qwen14b_instrumented_eval", path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Avoid executing main side effects; loader still runs module body.
    spec.loader.exec_module(mod)
    return mod


def test_scenario_filter_selects_g1_p1_only(monkeypatch):
    mod = _load_eval_module()
    monkeypatch.setenv(
        "DELIA_EVAL_SCENARIO_IDS",
        "G1_semantic_reword_structure,P1_product_structure_control",
    )
    selected = mod._selected_scenarios()
    assert [s["id"] for s in selected] == [
        "G1_semantic_reword_structure",
        "P1_product_structure_control",
    ]
    assert "P3_visualization_formats" not in {s["id"] for s in selected}


def test_scenario_filter_default_keeps_historical_list(monkeypatch):
    mod = _load_eval_module()
    monkeypatch.delenv("DELIA_EVAL_SCENARIO_IDS", raising=False)
    selected = mod._selected_scenarios()
    assert [s["id"] for s in selected] == [s["id"] for s in mod.SCENARIOS]
