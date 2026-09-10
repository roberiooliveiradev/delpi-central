"""E6.S4 — recommendationQueries como LEGACY_FALLBACK; dual-run candidate vs static."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.services.chat_contextual_recommendation_producer_service import (
    ChatContextualRecommendationProducerService,
)
from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_recommendation_grounding_service import (
    ChatRecommendationGroundingService,
)

_ROOT = Path(__file__).resolve().parents[4]
_PROFILES = _ROOT / "app/content/pt-BR/assistant/presentation_profiles.json"


def _commentary_profile_keys() -> list[str]:
    payload = json.loads(_PROFILES.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") or {}
    keys = sorted(
        {
            str(p.get("commentaryProfileKey") or "").strip()
            for p in profiles.values()
            if isinstance(p, dict) and str(p.get("commentaryProfileKey") or "").strip()
        }
    )
    return keys


def test_e6_s4_stock_candidate_subset_of_static_no_false_suggestions():
    grounding = ChatRecommendationGroundingService.build(
        profile_key="stock",
        facts=["Disponível 10"],
        limitations=["Período da consulta atual"],
    )
    result = ChatContextualRecommendationProducerService.produce_with_dual_run(
        grounding=grounding,
    )
    dual = result.dual_run
    assert dual.authority == "contextual_candidate"
    assert dual.used_profile_fallback is False
    assert dual.false_suggestion_count == 0
    assert dual.only_in_candidate == ()
    assert any("página" in q.casefold() for q in dual.only_in_static)
    assert all(item.get("source") == "deterministic" for item in result.items)


def test_e6_s4_all_important_profiles_have_non_empty_or_explicit_fallback():
    """Candidate cobre profiles com queries; false suggestions = 0 no path profile-derived."""

    keys = _commentary_profile_keys()
    assert len(keys) == 13
    empty_static: list[str] = []
    failures: list[str] = []

    for key in keys:
        static = ChatHumanizedDataResponseContentService.recommendation_queries(key)
        if not static:
            empty_static.append(key)
            continue
        grounding = ChatRecommendationGroundingService.build(profile_key=key)
        result = ChatContextualRecommendationProducerService.produce_with_dual_run(
            grounding=grounding,
            profile_queries=static,
        )
        if not result.items:
            failures.append(f"{key}: empty candidate and fallback")
            continue
        if result.dual_run.false_suggestion_count != 0:
            failures.append(
                f"{key}: falseSuggestionCount={result.dual_run.false_suggestion_count}"
            )
        if result.dual_run.authority not in {
            "contextual_candidate",
            "profile_fallback",
        }:
            failures.append(f"{key}: authority={result.dual_run.authority}")

    assert not empty_static
    assert not failures, failures


def test_e6_s4_attach_writes_dual_run_metadata():
    commentary = {"facts": ["a"], "limitations": ["sem truncamento"]}
    ChatDataInsightService._attach_turn_structured_recommendations(
        commentary,
        profile_key="stock",
        metadata={},
    )
    dual = commentary.get("recommendationDualRun") or {}
    assert dual.get("authority") == "contextual_candidate"
    assert dual.get("falseSuggestionCount") == 0
    assert dual.get("usedProfileFallback") is False
    assert commentary.get("structuredRecommendations")


def test_e6_s4_llm_candidates_may_diverge_from_static():
    grounding = ChatRecommendationGroundingService.build(profile_key="stock")
    result = ChatContextualRecommendationProducerService.produce_with_dual_run(
        grounding=grounding,
        llm_candidates=[
            {
                "label": "Nova",
                "query": "consulta inventada contextual",
                "source": "llm_contextual",
                "confidence": 0.9,
            }
        ],
    )
    assert result.dual_run.authority == "llm_or_existing"
    assert result.dual_run.false_suggestion_count == 1
    assert result.items[0]["source"] == "llm_contextual"


def test_e6_s4_fallback_when_all_queries_filtered_out():
    """Se todo o catálogo for paginação sem sinal → LEGACY_FALLBACK seguro."""

    grounding = ChatRecommendationGroundingService.build(
        profile_key="stock",
        limitations=["ok"],
    )
    only_pagination = [
        {
            "label": "Próxima",
            "query": "Mostrar a próxima página de estoque",
            "reason": "x",
        }
    ]
    result = ChatContextualRecommendationProducerService.produce_with_dual_run(
        grounding=grounding,
        profile_queries=only_pagination,
    )
    assert result.dual_run.used_profile_fallback is True
    assert result.dual_run.authority == "profile_fallback"
    assert result.items
    assert result.items[0]["source"] == "profile_fallback"
