"""Lean Six Sigma family on Methodology Intelligence V2.

V1 stays the frozen 13-method catalog. New ids resolve only on V2.
"""

from __future__ import annotations

import json

import pytest

from tm_app.application.methodology.guide import (
    list_method_ids,
    query_methodology_guide,
)
from tm_app.application.methodology.guide_v2 import (
    query_methodology_guide_v2,
)
from tm_app.application.methodology.lean_six_sigma import (
    LEAN_SIX_SIGMA_FAMILY,
    LSS_METHOD_IDS,
)


_V1 = {
    "macroprocess",
    "key_process",
    "end_to_end",
    "sipoc",
    "lean",
    "ishikawa",
    "five_whys",
    "ctp",
    "tdr",
    "kpi",
    "swot",
    "as_is",
    "to_be",
}


def test_v1_catalog_does_not_gain_lean_six_sigma_ids() -> None:
    assert set(list_method_ids()) == _V1
    with pytest.raises(ValueError, match="Unknown methodology method"):
        query_methodology_guide(method="pareto")
    sipoc = query_methodology_guide(method="sipoc")
    assert sipoc["guide_version"] == "teo-method-playbooks-v1"
    assert sipoc["method"]["id"] == "sipoc"


def test_v2_loads_family_without_replacing_legacy_methods() -> None:
    data = query_methodology_guide_v2()
    ids = {item["id"] for item in data["methods"]}
    assert _V1 <= ids
    assert set(LSS_METHOD_IDS) <= ids
    assert data["lean_six_sigma"]["competence"] == [
        "yellow_belt",
        "green_belt",
        "black_belt",
    ]
    assert "sipoc" in data["lean_six_sigma"]["existing_tools_reused"]


@pytest.mark.parametrize(
    "method_id, kind",
    [
        ("yellow_belt", "competence"),
        ("green_belt", "competence"),
        ("black_belt", "competence"),
        ("dmaic", "framework"),
        ("pareto", "tool"),
        ("msa", "tool"),
        ("fmea", "tool"),
    ],
)
def test_playbook_is_guidance_not_a_calculator(method_id: str, kind: str) -> None:
    data = query_methodology_guide_v2(method=method_id)
    method = data["method"]
    assert data["guide_version"] == "teo-method-playbooks-v2"
    assert method["kind"] == kind
    assert method["computes_statistics"] is False
    assert method["certifies"] is False
    assert method["persists"] is False
    blob = json.dumps(method)
    assert "ISO 13053" in blob or "certif" in blob.lower() or kind == "tool"
    if method_id in {"msa", "process_capability", "pareto", "hypothesis_test"}:
        assert "UNKNOWN" in blob or "invent" in blob.lower() or "No statistical" in blob


def test_dmaic_phases_and_epistemic_split() -> None:
    method = query_methodology_guide_v2(method="dmaic")["method"]
    steps = " ".join(method["steps"])
    for phase in ("DEFINE", "MEASURE", "ANALYZE", "IMPROVE", "CONTROL"):
        assert phase in steps
    assert "INFERRED" in json.dumps(method["epistemic_constraints"])
    assert "PROPOSED" in steps


def test_unknown_method_still_fails() -> None:
    with pytest.raises(ValueError, match="Unknown methodology method"):
        query_methodology_guide_v2(method="get_any_prompt")


def test_scenario_material_shortage_does_not_declare_a_cause() -> None:
    """Recurring material shortage: investigate, do not crown a cause."""
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"problem_defined": "yes"},
    )
    assert routed["resolved_intent"] == "diagnose"
    assert routed["candidate_hint"] == "ishikawa"
    play = query_methodology_guide_v2(method="ishikawa")["method"]
    blob = json.dumps(play)
    assert "proven" in blob
    assert "INFERRED" in blob


def test_scenario_scrap_selects_pareto_not_a_proven_cause() -> None:
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"problem_defined": "yes", "defect_concentration": "yes"},
    )
    assert routed["resolved_intent"] == "diagnose"
    assert routed["candidate_hint"] == "pareto"
    pareto = query_methodology_guide_v2(method="pareto")["method"]
    assert "proven" in json.dumps(pareto).lower() or "not a proven" in json.dumps(
        pareto["epistemic_constraints"]
    )


def test_scenario_dimensional_variation_asks_for_msa_first() -> None:
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"quality_variation": "yes"},
    )
    assert routed["resolved_intent"] == "measure"
    assert routed["candidate_hint"] == "msa"
    capability = query_methodology_guide_v2(
        method="process_capability",
        context={"quality_variation": "yes"},
    )
    assert capability["method"]["readiness"] != "READY"


def test_scenario_approval_delay_maps_before_statistics() -> None:
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"administrative_delay": "yes", "problem_defined": "yes"},
    )
    assert routed["resolved_intent"] == "map"
    assert routed["candidate_hint"] == "end_to_end"
    assert "hypothesis_test" not in {
        c["method_id"] for c in routed["candidates"] if c.get("favored")
    }


def test_scenario_regression_checks_control_not_a_new_project() -> None:
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"improvement_regressed": "yes", "problem_defined": "yes"},
    )
    assert routed["candidate_hint"] == "control_plan"
    plan = query_methodology_guide_v2(method="control_plan")["method"]
    assert "baseline" in json.dumps(plan).lower() or "indicator" in json.dumps(plan).lower()


def test_scenario_mapping_only_does_not_open_dmaic() -> None:
    routed = query_methodology_guide_v2(
        intent="improve",
        context={"mapping_only": "yes", "problem_defined": "yes"},
    )
    assert routed["resolved_intent"] == "map"
    assert routed["candidate_hint"] == "as_is"
    dmaic = query_methodology_guide_v2(
        method="dmaic",
        context={"mapping_only": "yes", "problem_defined": "yes"},
    )
    assert dmaic["method"]["readiness"] != "READY"


def test_family_reuses_legacy_ids() -> None:
    assert set(LEAN_SIX_SIGMA_FAMILY["existing_tools_reused"]) <= _V1
    lean = query_methodology_guide(method="lean")
    assert lean["method"]["id"] == "lean"
    assert "family" not in lean["method"]
