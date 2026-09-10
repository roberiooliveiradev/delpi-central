"""E6.S3 — producer contextual de recommendations (delta LLM=0)."""

from __future__ import annotations

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


def test_e6_s3_skips_pagination_query_without_truncation_signal():
    grounding = ChatRecommendationGroundingService.build(
        profile_key="stock",
        facts=["Disponível 10"],
        limitations=["Período da consulta atual"],
    )
    queries = ChatHumanizedDataResponseContentService.recommendation_queries("stock")
    produced = ChatContextualRecommendationProducerService.produce(
        grounding=grounding,
        profile_queries=queries,
    )
    assert produced
    assert all(item.get("source") == "deterministic" for item in produced)
    assert not any("página" in str(item.get("query") or "").casefold() for item in produced)
    assert len(produced) < len(queries)


def test_e6_s3_keeps_pagination_query_when_limitation_signals_truncation():
    grounding = ChatRecommendationGroundingService.build(
        profile_key="stock",
        limitations=["Lista truncada; peça a próxima página se necessário"],
    )
    queries = ChatHumanizedDataResponseContentService.recommendation_queries("stock")
    produced = ChatContextualRecommendationProducerService.produce(
        grounding=grounding,
        profile_queries=queries,
    )
    assert any("página" in str(item.get("query") or "").casefold() for item in produced)


def test_e6_s3_prefers_llm_candidates_and_drops_unauthorized():
    grounding = ChatRecommendationGroundingService.build(
        allowed_action_ids=["get_product_structure"],
        already_executed_action_ids=["get_product_stock"],
    )
    produced = ChatContextualRecommendationProducerService.produce(
        grounding=grounding,
        profile_queries=[{"label": "Ignorar", "query": "profile estático"}],
        llm_candidates=[
            {
                "label": "Estrutura",
                "query": "Mostrar estrutura",
                "actionId": "get_product_structure",
                "source": "llm_contextual",
                "confidence": 0.9,
            },
            {
                "label": "Hack",
                "query": "hack",
                "actionId": "delete_everything",
                "source": "llm_contextual",
            },
            {
                "label": "Malformed",
                "source": "llm_contextual",
            },
            {
                "label": "Já executou stock",
                "query": "estoque de novo",
                "actionId": "get_product_stock",
                "source": "llm_contextual",
            },
        ],
    )
    queries = {item["query"] for item in produced}
    assert queries == {"Mostrar estrutura"}
    assert produced[0]["source"] == "llm_contextual"


def test_e6_s3_empty_result_when_no_profile_and_no_candidates():
    grounding = ChatRecommendationGroundingService.build(profile_key="profile_inexistente")
    produced = ChatContextualRecommendationProducerService.produce(
        grounding=grounding,
        profile_queries=[],
        llm_candidates=[],
    )
    assert produced == []


def test_e6_s3_attach_wires_source_on_data_answer():
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
    recommendations = data_answer.get("recommendations") or []
    assert recommendations
    # source pode ser stripado no to_data_answer — structured path no commentary
    # Garante ao menos label/query do producer contextual.
    assert recommendations[0].get("label")
    assert recommendations[0].get("query")
    assert recommendations[0].get("source") == "deterministic"
    assert not any(
        "página" in str(r.get("query") or "").casefold() for r in recommendations
    )


def test_e6_s3_dedupe_duplicate_queries():
    grounding = ChatRecommendationGroundingService.build(profile_key="stock")
    produced = ChatContextualRecommendationProducerService.produce(
        grounding=grounding,
        llm_candidates=[
            {"label": "A", "query": "Mesma query", "source": "llm_contextual"},
            {"label": "B", "query": "mesma query", "source": "llm_contextual"},
        ],
    )
    assert len(produced) == 1
