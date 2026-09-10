"""E6.S2 — contrato de grounding para recomendações contextuais (input bounded)."""

from __future__ import annotations

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_recommendation_grounding_service import (
    ChatRecommendationGroundingService,
)


def test_e6_s2_build_includes_minimum_fields_without_raw_payload():
    huge_rows = [{"sku": f"X{i}", "qty": i} for i in range(500)]
    ctx = ChatRecommendationGroundingService.build(
        user_message="estoque do 10080001",
        user_goals=["ver estoque"],
        facts=["Disponível 10 na filial 01"],
        limitations=["Lista paginada"],
        allowed_action_ids=["get_product_stock", "get_product_structure"],
        already_executed_action_ids=["get_product_stock"],
        already_executed_goal_ids=["g1"],
        profile_key="stock",
        execution_results=[
            {
                "actionId": "get_product_stock",
                "ok": True,
                "path": "/products/10080001/stock",
                "data": {"items": huge_rows},
            }
        ],
        raw_data={"items": huge_rows},
    )
    payload = ctx.as_dict()
    assert payload["userMessage"] == "estoque do 10080001"
    assert payload["userGoals"] == ["ver estoque"]
    assert payload["facts"] == ["Disponível 10 na filial 01"]
    assert payload["limitations"] == ["Lista paginada"]
    assert "get_product_stock" in payload["allowedActionIds"]
    assert payload["alreadyExecutedActionIds"] == ["get_product_stock"]
    assert payload["alreadyExecutedGoalIds"] == ["g1"]
    assert payload["profileKey"] == "stock"
    assert payload["resultRefs"]
    assert payload["resultRefs"][0]["actionId"] == "get_product_stock"
    blob = str(payload)
    assert "X499" not in blob
    assert "raw_data" not in payload
    assert "data" not in payload


def test_e6_s2_caps_truncate_facts_and_message():
    caps = ChatHumanizedDataResponseContentService.recommendation_grounding_caps()
    long_fact = "f" * (caps["maxFactChars"] + 50)
    many_facts = [f"fato-{i}" for i in range(caps["maxFacts"] + 5)]
    long_msg = "m" * (caps["maxMessageChars"] + 80)
    ctx = ChatRecommendationGroundingService.build(
        user_message=long_msg,
        facts=[long_fact, *many_facts],
    )
    assert ctx.truncated is True
    assert len(ctx.user_message) == caps["maxMessageChars"]
    assert len(ctx.facts) == caps["maxFacts"]
    assert len(ctx.facts[0]) == caps["maxFactChars"]


def test_e6_s2_collects_fulfilled_goals_from_goal_coverage_metadata():
    ctx = ChatRecommendationGroundingService.build(
        metadata={
            "goalCoverage": {
                "results": [
                    {"goalId": "g1", "status": "fulfilled"},
                    {"goalId": "g2", "status": "partial"},
                    {"goalId": "g3", "status": "fulfilled"},
                ]
            }
        }
    )
    assert ctx.already_executed_goal_ids == ("g1", "g3")


def test_e6_s2_filter_drops_unauthorized_and_already_executed_action():
    grounding = ChatRecommendationGroundingService.build(
        allowed_action_ids=["get_product_stock"],
        already_executed_action_ids=["get_product_stock"],
    )
    filtered = ChatRecommendationGroundingService.filter_candidates_against_grounding(
        [
            {
                "label": "Estoque",
                "query": "ver estoque",
                "actionId": "get_product_stock",
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
                "label": "Estrutura",
                "query": "ver estrutura",
                "source": "llm_contextual",
                "confidence": 0.7,
            },
        ],
        grounding,
    )
    queries = {item["query"] for item in filtered}
    assert "hack" not in queries
    assert "ver estoque" not in queries  # already executed actionId
    assert "ver estrutura" in queries
    assert filtered[0]["source"] == "llm_contextual"


def test_e6_s2_parse_candidate_normalizes_source_and_confidence():
    candidate = ChatRecommendationGroundingService.parse_candidate(
        {
            "label": "Comparar período",
            "query": "Compare com o período anterior",
            "reason": "tendência",
            "source": "llm_contextual",
            "confidence": 1.5,
        }
    )
    assert candidate is not None
    assert candidate.source == "llm_contextual"
    assert candidate.confidence == 1.0
    bad = ChatRecommendationGroundingService.parse_candidate({"label": "x"})
    assert bad is None
    unknown_source = ChatRecommendationGroundingService.parse_candidate(
        {"label": "A", "query": "B", "source": "invented"}
    )
    assert unknown_source is not None
    assert unknown_source.source == "deterministic"


def test_e6_s2_empty_inputs_yield_empty_bounded_context():
    ctx = ChatRecommendationGroundingService.build()
    assert ctx.user_message == ""
    assert ctx.user_goals == ()
    assert ctx.facts == ()
    assert ctx.truncated is False
