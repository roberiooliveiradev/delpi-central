"""PHASE 5 — design methodology contract tests over the frozen corpus.

Machine-checkable expectations live in tests/design_methodology_corpus.py
(frozen before implementation). Subjective cases are flagged
NEEDS_HUMAN_RUBRIC — never auto-graded.
"""

from __future__ import annotations

import json

import pytest

from tests.design_methodology_corpus import CORPUS, HUMAN_RUBRIC_CASES

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)

READINESS = {"READY", "PARTIAL", "MISSING_INFORMATION", "BLOCKED"}
EPISTEMIC = {"FACT", "INFERRED", "RECOMMENDED", "UNKNOWN"}
INTENTS = {
    "REVIEW_SLIDE",
    "CHOOSE_VISUAL",
    "IMPROVE_EXISTING",
    "COMPOSE_SLIDE",
    "FIX_LAYOUT",
}


def _eval(case: dict) -> dict:
    fx = case["fixture"]
    digest = None
    if isinstance(fx.get("rows"), list):
        digest = DesignIntelligenceService.semantic_digest(
            fx["rows"], columns=fx.get("columns")
        )
    selection = fx.get("selection") or {}
    result = DesignIntelligenceService.evaluate_methodology(
        intent=case["intent"],
        digest=digest,
        design_audit=fx.get("audit"),
        selected_objects=selection.get("selectedObjects") or [],
        missing_ids=selection.get("missingIds") or [],
        selection_state=selection.get("selectionState"),
        canonical_pixels=fx.get("pixels"),
        extra_missing_readable=fx.get("missing_readable") or [],
        extra_missing_user=fx.get("missing_user") or [],
        has_data_source=bool(fx.get("has_data_source")),
        explicit_user_choice=fx.get("explicit_choice"),
        dominant_family=fx.get("dominant_family"),
        preview_error=fx.get("preview_error"),
    )
    return result


# -- contract schema ----------------------------------------------------------


def test_methodology_contract_closed_vocabularies():
    contract = DesignIntelligenceService._methodology_contract()
    assert contract["version"] == "design-methodology-v1"
    assert set(contract["readinessStates"]) == READINESS
    assert set(contract["epistemicStates"]) == EPISTEMIC
    assert set(contract["intents"]) == INTENTS
    assert contract["sufficiencyOutcomes"] == [
        "RECOMMEND_NOW",
        "READ_MORE_STATE",
        "ASK_USER",
        "NO_SAFE_RECOMMENDATION",
    ]
    assert contract["forbiddenClaims"]
    assert contract["readBeforeAsk"]["capabilities"]


def test_methodology_fact_refs_resolve():
    contract = DesignIntelligenceService._methodology_contract()
    sources = contract["factSources"]
    for intent, req in contract["factRequirements"].items():
        for fact in req.get("required", []) + req.get("optional", []):
            assert fact in sources, f"{intent}: fact {fact} has no source"
        assert intent in INTENTS


def test_contract_projected_in_catalog():
    surface = DesignIntelligenceService.catalog_projection()
    methodology = surface["designMethodology"]
    assert methodology["version"] == "design-methodology-v1"
    assert "designMethodology" in surface["fields"]
    # compact — no prose summaries in the catalog projection
    assert len(json.dumps(methodology)) < 8192


def test_no_numeric_confidence_in_methodology_output():
    case = next(c for c in CORPUS if c["id"] == "time_series_trend")
    result = _eval(case)
    assert "confidence" not in json.dumps(result)
    assert result["strategy"]["epistemic"] == "RECOMMENDED"


# -- corpus cases --------------------------------------------------------------


@pytest.mark.parametrize("case", CORPUS, ids=[c["id"] for c in CORPUS])
def test_corpus_case(case: dict):
    result = _eval(case)
    exp = case["expect"]
    assert result["readiness"] in READINESS
    if "readiness" in exp:
        assert result["readiness"] == exp["readiness"]
    if "readiness_in" in exp:
        assert result["readiness"] in exp["readiness_in"]
    strategy = result.get("strategy") or {}
    if "family_in" in exp:
        assert strategy.get("visualFamily") in exp["family_in"]
    if "family_not_in" in exp:
        assert strategy.get("visualFamily") not in exp["family_not_in"]
        rejected = {r.get("type") for r in strategy.get("rejected") or []}
        chosen = {strategy.get("visualFamily")}
        assert not (chosen & exp["family_not_in"])
    if exp.get("fabricated") is False:
        assert result.get("_fabricated") is False
    if exp.get("next_action") == "READ":
        assert result["sufficiency"] == "READ_MORE_STATE"
        assert (result.get("nextAction") or {}).get("kind") == "READ"
    if "read_capability_in" in exp:
        assert (result.get("nextAction") or {}).get("capability") in exp["read_capability_in"]
    if exp.get("next_question_only_for"):
        nq = result.get("nextQuestion") or {}
        assert nq.get("fact") == exp["next_question_only_for"]
    if exp.get("missing_fact"):
        assert any(
            m["fact"] == exp["missing_fact"] for m in result["missingFacts"]
        )
    if exp.get("no_target_guess"):
        target = result["facts"].get("target_object") or {}
        assert not target.get("value")
    if exp.get("target_id"):
        assert result["facts"]["target_object"]["value"] == exp["target_id"]
    if "evidence_level_in" in exp:
        assert result["evidence"]["level"] in exp["evidence_level_in"]
    if exp.get("aesthetic_claim_blocked_without_pixels"):
        assert result["evidence"]["level"] not in {"PIXELS_INSPECTED", "HUMAN_JUDGMENT"}
        assert result.get("aestheticGate") == "PIXELS_REQUIRED_FOR_AESTHETIC_CLAIMS"
    if exp.get("explicit_choice_preserved"):
        choice = (result.get("strategy") or {}).get("explicitUserChoice") or {}
        assert choice.get("respected") is True
        assert choice.get("visualFamily") == case["fixture"]["explicit_choice"]


def test_human_rubric_cases_flagged():
    for case_id in HUMAN_RUBRIC_CASES:
        case = next(c for c in CORPUS if c["id"] == case_id)
        result = _eval(case)
        # methodology never emits deterministic aesthetic grades
        assert result.get("_fabricated") is False
        if result["evidence"]["level"] not in {"PIXELS_INSPECTED", "HUMAN_JUDGMENT"}:
            assert result.get("aestheticGate") != "PIXELS_INSPECTED"


# -- gating / bypass ------------------------------------------------------------


def test_direct_commands_bypass_methodology():
    for msg in (
        "Aumente esse título",
        "Aumente a fonte",
        "Alinhe esses blocos à esquerda",
        "Crie um novo texto",
        "Delete este bloco",
        "Troque para gráfico de barras",
    ):
        assert DesignIntelligenceService.design_intent_for_message(msg) is None


def test_design_intents_detected():
    assert (
        DesignIntelligenceService.design_intent_for_message("melhore isso")
        == "IMPROVE_EXISTING"
    )
    assert (
        DesignIntelligenceService.design_intent_for_message("Qual gráfico devo usar?")
        == "CHOOSE_VISUAL"
    )
    assert (
        DesignIntelligenceService.design_intent_for_message("organize melhor esse slide")
        == "FIX_LAYOUT"
    )
    assert (
        DesignIntelligenceService.design_intent_for_message("deixe isso mais executivo")
        == "COMPOSE_SLIDE"
    )
    assert (
        DesignIntelligenceService.design_intent_for_message("esse slide está bom?")
        == "REVIEW_SLIDE"
    )


def test_preview_error_blocks_methodology():
    result = DesignIntelligenceService.evaluate_methodology(
        intent="CHOOSE_VISUAL",
        preview_error={"code": "DATA_RESOLUTION_FAILED", "message": "x"},
        has_data_source=True,
    )
    assert result["readiness"] == "BLOCKED"
    assert result["sufficiency"] == "NO_SAFE_RECOMMENDATION"
    assert result["strategy"] is None


def test_confidence_status_marked_legacy():
    digest = DesignIntelligenceService.semantic_digest(
        [{"date": "2026-01-01", "v": 1.0}], columns=["date", "v"]
    )
    rec = DesignIntelligenceService.visual_recommendation(digest)
    assert rec["confidenceStatus"] == "LEGACY_UNCALIBRATED"


# -- suggest_change integration ------------------------------------------------

from types import SimpleNamespace  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from tv_app.application.gpt_actions.dispatch_service import (  # noqa: E402
    GptActionsDispatchService,
)


def _dispatch() -> GptActionsDispatchService:
    return GptActionsDispatchService(repo=MagicMock(), writes=MagicMock(), commit=MagicMock())


def _user(uid: str = "u1"):
    return SimpleNamespace(is_superadmin=True, permissions=[], id=uid)


def _suggest(dispatch, message, host=None):
    with patch(
        "tv_app.application.gpt_actions.dispatch_service.assert_permission",
        return_value=None,
    ):
        return dispatch.suggest_change(
            user=_user(), message=message, host_context=host or {}, authorization=None
        )


def test_suggest_design_intent_attaches_methodology():
    payload = _suggest(_dispatch(), "melhore isso", host={"selectedBlockIds": ["t1"], "selectedBlockTypes": ["text"]})
    methodology = payload.get("designMethodology")
    assert methodology is not None
    assert methodology["designIntent"] == "IMPROVE_EXISTING"
    assert methodology["facts"]["target_object"]["value"] == "t1"
    assert methodology["readiness"] in READINESS


def test_suggest_direct_command_bypasses_methodology():
    payload = _suggest(_dispatch(), "Delete este bloco", host={})
    assert "designMethodology" not in payload


def test_suggest_ambiguous_selection_no_guess():
    payload = _suggest(
        _dispatch(),
        "melhore isso",
        host={"selectedBlockIds": ["a", "b"], "selectedBlockTypes": ["text", "kpi_view"]},
    )
    methodology = payload.get("designMethodology")
    assert methodology["readiness"] == "MISSING_INFORMATION"
    assert not methodology["facts"]["target_object"].get("value")
    assert methodology["sufficiency"] == "ASK_USER"


def test_suggest_methodology_does_not_change_ops():
    plain = _suggest(_dispatch(), "Crie um novo bloco de texto", host={})
    assert "designMethodology" not in plain
    payload = _suggest(_dispatch(), "melhore isso", host={})
    # advisory never fabricates ops
    assert payload["ops"] == []
    assert payload["designMethodology"]["sufficiency"] in {
        "READ_MORE_STATE",
        "ASK_USER",
        "RECOMMEND_NOW",
        "NO_SAFE_RECOMMENDATION",
    }
