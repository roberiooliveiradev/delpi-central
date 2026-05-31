from unittest.mock import patch

from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.chat_web_search_planning_service import (
    ChatWebSearchPlanningService,
)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_plan_quick_mode_default(_enabled):
    plan = ChatWebSearchPlanningService.plan(
        "pesquise na internet sobre clima em sao paulo"
    )

    assert plan is not None
    assert plan.mode == "quick"
    assert plan.max_results <= 3
    assert plan.primary_query()
    assert len(plan.queries) <= 3


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_plan_deep_mode_with_official_queries(_enabled):
    plan = ChatWebSearchPlanningService.plan(
        "pesquisa profunda na web sobre manual oficial WEG CFW500"
    )

    assert plan is not None
    assert plan.mode == "deep"
    assert plan.prefer_official is True
    assert plan.intent == "technical_document_search"
    assert any("site:weg.net" in query for query in plan.queries)
    assert any("manual oficial" in query for query in plan.queries)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_includes_planned_queries(_enabled):
    result = ChatWebSearchIntentService.resolve(
        "busque na web sobre datasheet motor WEG W22"
    )

    assert result is not None
    args = result["arguments"]
    assert args["searchMode"] in {"quick", "deep"}
    assert isinstance(args.get("plannedQueries"), list)
    assert len(args["plannedQueries"]) >= 1
    assert args["query"] == args["plannedQueries"][0]
