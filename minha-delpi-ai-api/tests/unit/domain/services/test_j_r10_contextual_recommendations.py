"""J-R10 — contextual recommendations; LEGACY_RECOMMENDATION_FALLBACK=0."""

from __future__ import annotations

from pathlib import Path

from app.domain.services.chat_contextual_recommendation_producer_service import (
    ChatContextualRecommendationProducerService,
)
from app.domain.services.chat_recommendation_grounding_service import (
    ChatRecommendationGroundingService,
)

_ROOT = Path(__file__).resolve().parents[4]
_PRODUCER = (
    _ROOT / "app/domain/services/chat_contextual_recommendation_producer_service.py"
)
_HUMANIZED = (
    _ROOT / "app/domain/services/chat_humanized_data_response_service.py"
)


def test_j_r10_producer_has_zero_legacy_fallback_authority():
    text = _PRODUCER.read_text(encoding="utf-8")
    assert "profile_fallback" not in text or 'source": "profile_fallback"' not in text
    assert "authority = \"profile_fallback\"" not in text
    assert "contextual_generic" in text
    assert "REMOVED" in text
    assert "legacyRecommendationFallback" in text


def test_j_r10_humanized_consumer_has_no_profile_fallback_dump():
    text = _HUMANIZED.read_text(encoding="utf-8")
    assert "LEGACY_FALLBACK" not in text
    assert 'source": "profile_fallback"' not in text


def test_j_r10_positive_goals_drive_generic_fallback():
    grounding = ChatRecommendationGroundingService.build(
        profile_key="stock",
        user_goals=["comparar cobertura de estoque"],
    )
    result = ChatContextualRecommendationProducerService.produce_with_dual_run(
        grounding=grounding,
        profile_queries=[],
    )
    assert result.dual_run.authority == "contextual_generic"
    assert result.items
    assert "comparar cobertura" in result.items[0]["query"].casefold()


def test_j_r10_negative_llm_still_preferred_over_generic():
    grounding = ChatRecommendationGroundingService.build(profile_key="stock")
    result = ChatContextualRecommendationProducerService.produce_with_dual_run(
        grounding=grounding,
        profile_queries=[],
        llm_candidates=[
            {
                "label": "LLM",
                "query": "consulta llm",
                "source": "llm_contextual",
            }
        ],
    )
    assert result.dual_run.authority == "llm_or_existing"
    assert result.items[0]["query"] == "consulta llm"
