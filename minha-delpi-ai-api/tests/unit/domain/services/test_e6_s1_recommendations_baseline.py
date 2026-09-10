"""E6.S1 — baseline freeze: recommendations (profile authority) + composer templates."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_composer_route_question_suggestion_service import (
    ChatComposerRouteQuestionSuggestionService,
)
from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.recommendation_action_validator import (
    RecommendationActionValidator,
)


@dataclass(frozen=True)
class RecsBaselineCase:
    family: str
    notes: str


# Frozen 2026-09-10 — authority atual (queries estáticas + composer heurístico).
_CORPUS: tuple[RecsBaselineCase, ...] = (
    RecsBaselineCase(
        family="profile_static_queries",
        notes="stock profile eleva recommendationQueries 1:1 para dataAnswer.recommendations",
    ),
    RecsBaselineCase(
        family="already_executed_no_dedupe",
        notes="mesmo após tool stock, queries estáticas do profile sobem (sem anti-redundância)",
    ),
    RecsBaselineCase(
        family="unauthorized_action_id",
        notes="actionId fora allowlist dropado; query sem actionId passa (gap R06-01)",
    ),
    RecsBaselineCase(
        family="existing_structured_skips_static",
        notes="se structuredRecommendations já existe, attach não sobrescreve",
    ),
    RecsBaselineCase(
        family="composer_prefix",
        notes="'analise' → route questions de desenho; query ≠ draft",
    ),
    RecsBaselineCase(
        family="composer_negative_short",
        notes="draft abaixo de minDraftLength → lista vazia",
    ),
)


def test_e6_s1_baseline_corpus_families():
    assert {c.family for c in _CORPUS} == {
        "profile_static_queries",
        "already_executed_no_dedupe",
        "unauthorized_action_id",
        "existing_structured_skips_static",
        "composer_prefix",
        "composer_negative_short",
    }


def test_profile_static_queries_match_json_authority():
    """Positive: producer atual = elevação estática do profile."""

    metadata = {
        "path": "/products/10080001/stock",
        "stackPresentationPlan": {"presentationProfileKey": "stock"},
        "tablePresentation": {
            "type": "table",
            "rows": [{"branch": "01", "warehouse": "01", "available": 10}],
        },
    }
    data_answer = ChatDataInsightService.build(
        metadata,
        {"items": [{"branch": "01", "warehouse": "01", "available": 10}]},
    )
    assert isinstance(data_answer, dict)
    profile_key = str(data_answer.get("profileKey") or "")
    recommendations = data_answer.get("recommendations") or []
    expected = ChatHumanizedDataResponseContentService.recommendation_queries(profile_key)
    assert expected, f"profile {profile_key} must have recommendationQueries"
    assert recommendations
    assert recommendations[0]["label"] == expected[0]["label"]
    assert recommendations[0]["query"] == expected[0]["query"]
    assert "source" not in recommendations[0]


def test_already_executed_no_dedupe_still_emits_profile_queries():
    """Sibling gap R06-02: metadata de action já executada não remove queries estáticas."""

    metadata = {
        "path": "/products/10080001/stock",
        "stackPresentationPlan": {"presentationProfileKey": "stock"},
        "executedActionIds": ["get_product_stock"],
        "tablePresentation": {
            "type": "table",
            "rows": [{"branch": "01", "available": 1}],
        },
    }
    data_answer = ChatDataInsightService.build(
        metadata,
        {"items": [{"branch": "01", "available": 1}]},
    )
    assert isinstance(data_answer, dict)
    expected = ChatHumanizedDataResponseContentService.recommendation_queries(
        str(data_answer.get("profileKey") or "")
    )
    recommendations = data_answer.get("recommendations") or []
    assert len(recommendations) == len(expected)
    assert recommendations[0]["query"] == expected[0]["query"]


def test_unauthorized_action_id_dropped_but_text_query_passes():
    """Negative R06-01 parcial: allowlist só age em actionId."""

    commentary = {
        "summary": "ok",
        "facts": ["a"],
        "highlights": ["a"],
        "profileKey": "stock",
        "allowedActionIds": ["get_product_stock"],
        "structuredRecommendations": [
            {
                "label": "Estoque ok",
                "query": "estoque",
                "actionId": "get_product_stock",
            },
            {
                "label": "Hack",
                "query": "hack",
                "actionId": "delete_everything",
            },
            {
                "label": "Texto livre inventado",
                "query": "executar ação secreta inexistente",
            },
        ],
    }
    data_answer = ChatHumanizedDataResponseService.to_data_answer(commentary)
    assert isinstance(data_answer, dict)
    recs = data_answer.get("recommendations") or []
    queries = {str(r.get("query") or "") for r in recs}
    assert "hack" not in queries
    assert "estoque" in queries
    assert "executar ação secreta inexistente" in queries

    filtered = RecommendationActionValidator.filter_items(
        commentary["structuredRecommendations"],
        allowed_action_ids={"get_product_stock"},
    )
    assert {i.get("query") for i in filtered} == {
        "estoque",
        "executar ação secreta inexistente",
    }


def test_existing_structured_skips_static_elevation():
    commentary = {
        "structuredRecommendations": [
            {"label": "Já veio do turno", "query": "consulta custom", "reason": "x"}
        ]
    }
    ChatDataInsightService._attach_turn_structured_recommendations(
        commentary,
        profile_key="stock",
        metadata={},
    )
    assert commentary["structuredRecommendations"][0]["label"] == "Já veio do turno"
    assert commentary["structuredRecommendations"][0]["query"] == "consulta custom"


def test_composer_prefix_offers_drawing_route_questions():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest("analise")
    assert suggestions
    assert any("desenho" in str(item.get("query") or "").casefold() for item in suggestions)
    assert all(item.get("query") != "analise" for item in suggestions)


def test_composer_negative_short_draft_returns_empty():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest("ab")
    assert suggestions == []


def test_recommendation_queries_cover_all_commentary_profile_keys():
    """Coverage gate D2 ainda vigente: 13 commentaryProfileKey ↔ recommendationQueries."""

    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[4]
    payload = json.loads(
        (root / "app/content/pt-BR/assistant/presentation_profiles.json").read_text(
            encoding="utf-8"
        )
    )
    profiles = payload.get("profiles") or {}
    keys = {
        str(p.get("commentaryProfileKey") or "").strip()
        for p in profiles.values()
        if isinstance(p, dict) and str(p.get("commentaryProfileKey") or "").strip()
    }
    assert len(keys) == 13
    missing = [
        k
        for k in sorted(keys)
        if not ChatHumanizedDataResponseContentService.recommendation_queries(k)
    ]
    assert not missing
