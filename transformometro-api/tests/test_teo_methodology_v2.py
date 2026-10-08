"""Methodology Intelligence V2 — contract, behavior and compatibility gates."""

from __future__ import annotations

import asyncio
import contextlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from pathlib import Path

import pytest
from fastapi.responses import JSONResponse

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.application.methodology.guide import (
    GUIDE_VERSION,
    list_method_ids,
    list_task_ids,
    query_methodology_guide,
)
from tm_app.application.methodology.guide_v2 import (
    COMPOSITION_EDGES,
    CONTEXT_FACTS,
    GUIDE_VERSION_V1,
    GUIDE_VERSION_V2,
    INTENT_IDS,
    QUESTION_KINDS,
    READINESS_STATES,
    RECOMMENDED_GUIDE_VERSION,
    STOP_REASONS,
    SUFFICIENCY_STATES,
    SUPPORTED_GUIDE_VERSIONS,
    WIRE_DEFAULT_GUIDE_VERSION,
    _METHOD_SEMANTICS,
    evaluate_readiness,
    evaluate_sufficiency,
    query_methodology_guide_v2,
    resolve_guide_version,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp.tool_bridge import tool_get_methodology_guide

_V1_METHODS = {
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
_V1_TASKS = {
    "discover",
    "map",
    "diagnose",
    "redesign",
    "measure",
    "prioritize",
    "interview",
}


def _user():
    return SimpleNamespace(
        id="u1",
        email="teo@example.com",
        name="Téo",
        roles=[],
        groups=[],
        permissions=["transformometro.view"],
        is_superadmin=False,
    )


@contextlib.contextmanager
def _allow():
    with patch(
        "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
        return_value=None,
    ):
        yield


def _ctx():
    u = set_current_user(_user())
    a = set_request_authorization("Bearer test")
    return u, a


def _reset(tokens):
    u, a = tokens
    reset_request_authorization(a)
    reset_current_user(u)


# --------------------------------------------------------------- V1 freeze


def test_v1_frozen_surface() -> None:
    assert set(list_method_ids()) == _V1_METHODS
    assert set(list_task_ids()) == _V1_TASKS
    assert GUIDE_VERSION == "teo-method-playbooks-v1"
    assert WIRE_DEFAULT_GUIDE_VERSION == GUIDE_VERSION_V1
    # Post-acceptance cutover: recommendation is V2; wire default stays V1.
    assert RECOMMENDED_GUIDE_VERSION == GUIDE_VERSION_V2


def test_legacy_call_still_returns_v1() -> None:
    data = query_methodology_guide()
    assert data["guide_version"] == "teo-method-playbooks-v1"
    assert data["read_only"] is True
    assert data["writes"] is False
    data = query_methodology_guide(method="ishikawa")
    assert data["guide_version"] == "teo-method-playbooks-v1"
    assert data["method"]["persists"] is False
    assert data["method"]["authorizes"] is False


def test_dispatch_default_and_explicit_v1() -> None:
    tokens = _ctx()
    try:
        with _allow():
            r1 = tool_get_methodology_guide(method="swot")
            r2 = tool_get_methodology_guide(
                method="swot", guide_version="teo-method-playbooks-v1"
            )
        for r in (r1, r2):
            assert r.is_error is False
            assert r.structured_content["data"]["guide_version"] == (
                "teo-method-playbooks-v1"
            )
    finally:
        _reset(tokens)


# --------------------------------------------------------------- versioning


def test_v2_selected_explicitly() -> None:
    tokens = _ctx()
    try:
        with _allow():
            r = tool_get_methodology_guide(
                guide_version="teo-method-playbooks-v2"
            )
        assert r.is_error is False
        data = r.structured_content["data"]
        assert data["guide_version"] == "teo-method-playbooks-v2"
        assert data["wire_default_version"] == "teo-method-playbooks-v1"
        assert data["recommended_version"] == "teo-method-playbooks-v2"
    finally:
        _reset(tokens)


def test_unknown_version_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown guide_version"):
        resolve_guide_version("teo-method-playbooks-v9")
    tokens = _ctx()
    try:
        with _allow():
            r = tool_get_methodology_guide(
                guide_version="teo-method-playbooks-v9"
            )
        assert r.is_error is True
        assert r.structured_content["status_code"] == 400
    finally:
        _reset(tokens)


def test_resolve_version_defaults() -> None:
    assert resolve_guide_version(None) == GUIDE_VERSION_V1
    assert resolve_guide_version("") == GUIDE_VERSION_V1
    assert resolve_guide_version("teo-method-playbooks-v2") == GUIDE_VERSION_V2


# --------------------------------------------------- contract / structural


def test_v2_semantics_cover_all_v1_methods() -> None:
    # Single semantic authority: every V1 method has exactly one V2 block.
    assert set(_METHOD_SEMANTICS) == set(list_method_ids())


def test_intents_and_references_valid() -> None:
    assert "strategic_analysis" in INTENT_IDS
    assert "improve" in INTENT_IDS
    all_methods = set(list_method_ids())
    for mid, sem in _METHOD_SEMANTICS.items():
        for intent in sem["intents"]:
            assert intent in INTENT_IDS
        for req in sem["minimum_information"]:
            assert req["fact"] in CONTEXT_FACTS
        for q in sem.get("gap_questions", ()):
            assert q["kind"] in QUESTION_KINDS
            assert q["resolves"] in CONTEXT_FACTS
    for edge in COMPOSITION_EDGES:
        assert edge["source_method"] in all_methods
        assert edge["target_method"] in all_methods
        assert edge["mandatory"] is False


def test_closed_vocabularies() -> None:
    assert set(READINESS_STATES) == {"READY", "PARTIAL", "NOT_READY", "UNKNOWN"}
    assert set(SUFFICIENCY_STATES) == {"SUFFICIENT", "NOT_SUFFICIENT", "UNKNOWN"}
    assert "PURPOSE_ACHIEVED" in STOP_REASONS
    assert "SPECULATION_RISK" in STOP_REASONS
    assert set(QUESTION_KINDS) == {
        "clarifying",
        "readiness",
        "evidence",
        "deepening",
    }


def test_no_duplicate_method_ids() -> None:
    ids = list_method_ids()
    assert len(ids) == len(set(ids))


def test_v2_read_only_flags() -> None:
    data = query_methodology_guide_v2(intent="diagnose")
    assert data["read_only"] is True
    assert data["writes"] is False
    assert data["persists"] is False
    assert data["authority"] == "GUIDANCE_NOT_SOURCE_OF_TRUTH"
    blob = json.dumps(data)
    assert "transformometro.view" not in blob
    assert "client_secret" not in blob


# ------------------------------------------------------------- behavior


def test_strategic_analysis_favors_swot() -> None:
    r = query_methodology_guide_v2(
        intent="strategic_analysis",
        context={
            "strategic_question": True,
            "scope_defined": True,
            "horizon_defined": True,
        },
    )
    top = r["candidates"][0]
    assert top["method_id"] == "swot"
    assert top["favored"] is True
    assert top["readiness"] == "READY"


def test_improve_without_context_does_not_pick_arbitrary_method() -> None:
    r = query_methodology_guide_v2(
        intent="improve", context={"process_identified": True}
    )
    assert r["resolved_intent"] is None
    assert "ambiguity" in r
    assert r["next_questions"][0]["kind"] == "clarifying"


def test_improve_meta_routes_known_problem() -> None:
    r = query_methodology_guide_v2(
        intent="improve",
        context={"problem_defined": True, "candidate_cause": "inferred"},
    )
    assert r["resolved_intent"] == "diagnose"
    assert r["candidate_hint"] == "five_whys"


def test_ishikawa_favored_with_open_causal_families() -> None:
    r = query_methodology_guide_v2(
        intent="diagnose",
        context={"problem_defined": True, "multiple_cause_families": True},
    )
    by_id = {c["method_id"]: c for c in r["candidates"]}
    assert by_id["ishikawa"]["favored"] is True
    assert by_id["five_whys"]["favored"] is False


def test_five_whys_favored_with_candidate_cause() -> None:
    r = query_methodology_guide_v2(
        intent="diagnose",
        context={"problem_defined": True, "candidate_cause": "inferred"},
    )
    by_id = {c["method_id"]: c for c in r["candidates"]}
    assert by_id["five_whys"]["favored"] is True
    assert by_id["five_whys"]["readiness"] == "READY"


def test_lean_favored_with_known_flow_and_waste() -> None:
    r = query_methodology_guide_v2(
        intent="diagnose",
        context={"flow_known": True, "waste_symptoms": True},
    )
    by_id = {c["method_id"]: c for c in r["candidates"]}
    assert by_id["lean"]["favored"] is True


def test_tdr_readiness_states() -> None:
    assert evaluate_readiness("tdr", {})["readiness"] == "UNKNOWN"
    assert (
        evaluate_readiness("tdr", {"as_is_known": False})["readiness"]
        == "NOT_READY"
    )
    assert (
        evaluate_readiness("tdr", {"as_is_known": True})["readiness"] == "READY"
    )


def test_to_be_output_stays_proposed() -> None:
    r = query_methodology_guide_v2(method="to_be")
    blob = json.dumps(r["method"])
    assert "PROPOSED" in blob
    assert "PROPOSED != SAVED" in r["invariants"]


def test_ishikawa_to_five_whys_is_optional() -> None:
    r = query_methodology_guide_v2(method="ishikawa")
    edges = r["method"]["suggested_next"]
    assert edges[0]["target_method"] == "five_whys"
    assert edges[0]["mandatory"] is False


def test_recorded_unknown_is_not_reasked() -> None:
    r1 = query_methodology_guide_v2(intent="diagnose")
    five = {c["method_id"]: c for c in r1["candidates"]}["five_whys"]
    assert five["readiness"] == "UNKNOWN"
    r2 = query_methodology_guide_v2(
        intent="diagnose",
        context={"recorded_unknowns": ["problem_defined", "candidate_cause"]},
    )
    texts = json.dumps(r2["next_questions"])
    assert "gap_problem_defined" not in texts
    assert "gap_candidate_cause" not in texts


def test_sipoc_applicable_when_suppliers_unknown() -> None:
    # SIPOC exists to discover suppliers/inputs — they are not preconditions.
    r = query_methodology_guide_v2(
        intent="map", context={"process_identified": True}
    )
    by_id = {c["method_id"]: c for c in r["candidates"]}
    assert by_id["sipoc"]["readiness"] == "READY"


def test_inferred_candidate_accepted_not_promoted() -> None:
    r = query_methodology_guide_v2(
        method="five_whys",
        context={"problem_defined": True, "candidate_cause": "inferred"},
    )
    assert r["method"]["readiness"] == "READY"
    blob = json.dumps(r)
    assert "INFERRED" in blob
    assert "proven" in blob or "INFERRED" in str(
        r["method"]["epistemic_constraints"]
    )


def test_swot_negative_signal_for_operational_cause() -> None:
    r = query_methodology_guide_v2(
        intent="strategic_analysis",
        context={
            "strategic_question": True,
            "scope_defined": True,
            "horizon_defined": True,
            "operational_cause_focus": True,
        },
    )
    swot = r["candidates"][0]
    assert swot["method_id"] == "swot"
    assert swot["favored"] is False
    assert "operational_cause_focus" in swot["signals_against"]


def test_sufficiency_non_blocking_unknown() -> None:
    out = evaluate_sufficiency(
        "five_whys",
        {
            "remaining_unknown_non_blocking": True,
            "next_question_low_materiality": True,
        },
    )
    assert out["sufficiency"] == "SUFFICIENT"
    assert set(out["stop_reasons"]) == {
        "REMAINING_UNKNOWN_NON_BLOCKING",
        "NEXT_QUESTION_LOW_MATERIALITY",
    }
    assert evaluate_sufficiency("kpi", {})["sufficiency"] == "UNKNOWN"
    assert (
        evaluate_sufficiency("kpi", {"speculation_risk": True})["sufficiency"]
        == "SUFFICIENT"
    )


def test_unknown_intent_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown methodology intent"):
        query_methodology_guide_v2(intent="delete_records")


def test_unknown_context_facts_ignored_not_fatal() -> None:
    r = query_methodology_guide_v2(
        intent="map", context={"process_identified": True, "bogus_fact": True}
    )
    assert r["ignored_context_facts"] == ["bogus_fact"]


# ------------------------------------------------------------ MCP contract


def test_mcp_tool_projects_version_and_intent() -> None:
    mcp = create_mcp_server()
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert len(tools) == 21  # workspace_context + product_guide + solution_read
    guide = tools["get_methodology_guide"]
    props = guide.input_schema["properties"]
    assert "guide_version" in props
    assert "intent" in props
    blob = json.dumps(props["guide_version"])
    assert "teo-method-playbooks-v1" in blob
    assert "teo-method-playbooks-v2" in blob
    blob = json.dumps(props["intent"])
    assert "strategic_analysis" in blob
    assert "improve" in blob


def test_mcp_bridge_v1_and_v2() -> None:
    tokens = _ctx()
    try:
        with _allow():
            v1 = tool_get_methodology_guide(method="lean")
        assert v1.structured_content["data"]["guide_version"] == (
            "teo-method-playbooks-v1"
        )
        with _allow():
            v2 = tool_get_methodology_guide(
                guide_version="teo-method-playbooks-v2",
                intent="strategic_analysis",
                context={
                    "strategic_question": True,
                    "scope_defined": True,
                    "horizon_defined": True,
                },
            )
        data = v2.structured_content["data"]
        assert data["guide_version"] == "teo-method-playbooks-v2"
        assert data["candidates"][0]["method_id"] == "swot"
        with _allow():
            v2m = tool_get_methodology_guide(
                guide_version="teo-method-playbooks-v2", intent="improve"
            )
        assert v2m.structured_content["data"]["meta_routing"] is True
    finally:
        _reset(tokens)


# --------------------------------------------------------------- catalog


def test_catalog_discovers_v2_without_duplicating_guide() -> None:
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )

    catalog = build_capability_surface_catalog("mcp")
    entry = {c["id"]: c for c in catalog["analyses"]}["methodology_guide"]
    meta = entry["methodology"]
    assert meta["supported_versions"] == [
        "teo-method-playbooks-v1",
        "teo-method-playbooks-v2",
    ]
    assert meta["wire_default_version"] == "teo-method-playbooks-v1"
    assert meta["recommended_version"] == "teo-method-playbooks-v2"
    assert set(meta["supported_v2_intents"]) == set(INTENT_IDS)
    # Catalog announces versions/intents only — full playbook stays in the guide.
    assert "methods" not in entry
    assert "playbooks" not in entry


# -------------------------------------------------------------- OpenAPI


def test_openapi_operation_unchanged_with_new_params() -> None:
    from tm_app.application.gpt_actions.openapi_builder import (
        build_gpt_actions_openapi,
    )

    doc = build_gpt_actions_openapi()
    path = f"{doc['servers'] and ''}/gpt-actions/methodology-guide"
    op = None
    for p, spec in doc["paths"].items():
        if p.endswith("/methodology-guide"):
            op = spec["get"]
            assert p.endswith("/methodology-guide")
    assert op is not None
    assert op["operationId"] == "gpt_get_methodology_guide"
    names = {p["name"] for p in op["parameters"]}
    assert {"method", "task", "guide_version", "intent", "context"} <= names
    gv = {p["name"]: p for p in op["parameters"]}["guide_version"]
    assert gv["schema"]["enum"] == [
        "teo-method-playbooks-v1",
        "teo-method-playbooks-v2",
    ]
    iv = {p["name"]: p for p in op["parameters"]}["intent"]
    assert set(iv["schema"]["enum"]) == set(INTENT_IDS)
    # operation count unchanged
    ops = [
        op2["operationId"]
        for spec in doc["paths"].values()
        for op2 in spec.values()
        if isinstance(op2, dict) and "operationId" in op2
    ]
    assert len(ops) == len(set(ops))
# ------------------------------------------------- Derived knowledge doc


def test_v2_markdown_is_derived_projection() -> None:
    """teo-method-playbooks-v2.md is generated - never edited by hand (single
    semantic authority; spec section 28)."""
    from tm_app.application.methodology.guide_v2 import render_v2_markdown

    doc = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "gpt-actions"
        / "teo-method-playbooks-v2.md"
    )
    assert doc.read_text(encoding="utf-8") == render_v2_markdown()


# ------------------------------------------- Hotfix: improve meta-routing


def test_improve_problem_defined_alone_resolves_diagnose() -> None:
    """Hotfix: problem_defined=yes must resolve to diagnose, never map."""
    r = query_methodology_guide_v2(
        intent="improve", context={"problem_defined": "yes"}
    )
    assert r["resolved_intent"] == "diagnose"
    assert r["resolved_intent"] != "map"
    # Semantics: Ishikawa favored/READY; Five Whys PARTIAL until a
    # candidate cause exists.
    by_id = {c["method_id"]: c for c in r["candidates"]}
    assert by_id["ishikawa"]["readiness"] == "READY"
    assert by_id["ishikawa"]["favored"] is True
    assert by_id["five_whys"]["readiness"] == "PARTIAL"


def test_improve_problem_plus_candidate_cause_favors_five_whys() -> None:
    r = query_methodology_guide_v2(
        intent="improve",
        context={"problem_defined": "yes", "candidate_cause": "inferred"},
    )
    assert r["resolved_intent"] == "diagnose"
    assert r["candidates"][0]["method_id"] == "five_whys"
    assert r["candidates"][0]["favored"] is True


def test_improve_strategic_frame_resolves_strategic_analysis() -> None:
    r = query_methodology_guide_v2(
        intent="improve",
        context={
            "strategic_question": "yes",
            "scope_defined": "yes",
            "horizon_defined": "yes",
        },
    )
    assert r["resolved_intent"] == "strategic_analysis"
    assert r["candidates"][0]["method_id"] == "swot"
    assert r["candidates"][0]["favored"] is True


def test_improve_as_is_plus_redesign_resolves_redesign_tdr() -> None:
    r = query_methodology_guide_v2(
        intent="improve",
        context={"as_is_known": "yes", "redesign_desired": "yes"},
    )
    assert r["resolved_intent"] == "redesign"
    assert r["candidates"][0]["method_id"] == "tdr"


def test_improve_flow_plus_waste_resolves_diagnose_lean() -> None:
    r = query_methodology_guide_v2(
        intent="improve",
        context={"flow_known": "yes", "waste_symptoms": "yes"},
    )
    assert r["resolved_intent"] == "diagnose"
    assert r["candidates"][0]["method_id"] == "lean"


def test_improve_indiscriminate_context_yields_clarifying_question() -> None:
    """Context that matches no routing rule must surface one discriminative
    question instead of a silent method pick."""
    # as_is_known=yes alone: no problem, no redesign, no flow waste, no
    # strategic frame -> no rule matches -> ambiguity, not map.
    r = query_methodology_guide_v2(
        intent="improve", context={"as_is_known": "yes"}
    )
    assert r.get("resolved_intent") is None
    questions = [q2 for q2 in r["next_questions"] if q2["kind"] == "clarifying"]
    assert questions and questions[0]["resolves"]


# ------------------------------------- Hotfix: context vocabulary contract


def test_context_fact_schema_is_single_authority() -> None:
    from tm_app.application.methodology.guide_v2 import (
        CONTEXT_FACT_SCHEMA,
        context_fact_schema,
    )

    # CONTEXT_FACTS derives from the schema — no second vocabulary list.
    assert CONTEXT_FACTS == tuple(CONTEXT_FACT_SCHEMA)
    projected = context_fact_schema()
    assert [f["id"] for f in projected] == list(CONTEXT_FACTS)
    for fact in projected:
        assert fact["description"]
        assert "yes" in fact["accepted_values"]
        assert "unknown" in fact["accepted_values"]


def test_v2_payload_advertises_supported_context_facts() -> None:
    r = query_methodology_guide_v2(intent="map")
    facts = r["supported_context_facts"]
    assert [f["id"] for f in facts] == list(CONTEXT_FACTS)
    ids = {f["id"] for f in facts}
    assert {"problem_defined", "candidate_cause", "waste_symptoms"} <= ids


def test_unknown_fact_ignored_but_vocabulary_discoverable() -> None:
    r = query_methodology_guide_v2(
        intent="diagnose",
        context={
            "problem_defined": "yes",
            "foo_bar": "yes",
            "multiple_causal_families": "yes",
        },
    )
    assert set(r["ignored_context_facts"]) == {
        "foo_bar",
        "multiple_causal_families",
    }
    # Deterministic discovery of the valid vocabulary in the same payload.
    assert [f["id"] for f in r["supported_context_facts"]] == list(
        CONTEXT_FACTS
    )
    assert "multiple_cause_families" in CONTEXT_FACTS
