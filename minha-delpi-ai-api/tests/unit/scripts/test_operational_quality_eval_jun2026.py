"""Sprint 5 — contrato offline dos scripts de homologação operacional (jun/2026)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tests.fixtures.chat_intelligence_regression_cases import (
    OPERATIONAL_QUALITY_JUN2026_CASES,
    OPERATIONAL_QUALITY_JUN2026_INDEX,
    SELECTION_CASES,
)


def _load_eval_script(filename: str):
    path = Path(__file__).resolve().parents[3] / "scripts" / filename

    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module


def test_operational_quality_jun2026_index_covers_pa_flow() -> None:
    assert len(OPERATIONAL_QUALITY_JUN2026_CASES) >= 6
    assert {item["id"] for item in OPERATIONAL_QUALITY_JUN2026_INDEX} == {
        case["id"] for case in OPERATIONAL_QUALITY_JUN2026_CASES
    }

    messages = {case["message"] for case in OPERATIONAL_QUALITY_JUN2026_CASES}

    assert "Qual o status completo na fábrica do produto 90260140 hoje?" in messages
    assert any("visão fabril integrada" in message for message in messages)
    assert any("Simule aumento de 10%" in message for message in messages)


def test_eval_real_product_flow_follow_ups_align_with_regression_map() -> None:
    module = _load_eval_script("eval_real_product_flow_jun2026.py")
    follow_ups = module.FOLLOW_UPS

    assert follow_ups
    assert set(module.MODES) == {"fast", "normal", "thinker"}

    expected_fragments = {case["expectedPath"] for case in follow_ups}

    for fragment in (
        "/factory-status",
        "/production-status",
        "/shipping-status",
        "/structure/exclusivity",
        "/raw-material-price-intelligence",
        "/cost-impact-simulation",
    ):
        assert fragment in expected_fragments

    regression_fragments = {
        case["expected_path_fragment"]
        for case in OPERATIONAL_QUALITY_JUN2026_CASES
        if case.get("expected_path_fragment")
    }

    for fragment in regression_fragments:
        assert fragment in expected_fragments


def test_eval_response_modes_script_declares_product_route_scenarios() -> None:
    module = _load_eval_script("eval_response_modes_product_routes_jun2026.py")

    scenarios = module.SCENARIOS
    modes = module.MODES

    assert scenarios
    assert set(modes) == {"fast", "normal", "thinker"}

    for scenario in scenarios:
        assert scenario.get("id")
        assert scenario.get("message")
        assert scenario.get("expectedPath")


@pytest.mark.parametrize("case", OPERATIONAL_QUALITY_JUN2026_CASES, ids=lambda c: c["id"])
def test_operational_quality_cases_not_duplicated_in_selection_cases(case: dict) -> None:
    duplicates = [
        item
        for item in SELECTION_CASES
        if item.get("message") == case.get("message")
        and item.get("expected_action_id") == case.get("expected_action_id")
    ]

    assert not duplicates, f"mensagem duplicada em SELECTION_CASES: {case['message']}"
