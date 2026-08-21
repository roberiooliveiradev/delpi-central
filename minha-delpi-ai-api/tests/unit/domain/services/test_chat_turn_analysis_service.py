from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_turn_analysis_content_service import (
    ChatTurnAnalysisContentService,
)
from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisService

configure_domain_infrastructure_ports()


def test_content_system_prompt_includes_limits():
    prompt = ChatTurnAnalysisContentService.system_prompt()
    assert "JSON" in prompt
    assert str(ChatTurnAnalysisContentService.max_action_ids()) in prompt


def test_parse_execute_filters_unknown_actions():
    raw = """
    {
      "decision": "execute",
      "intent": "operational_query",
      "subIntent": "stock_lookup",
      "skillsToLoad": ["sql", "unknown-skill"],
      "actionIds": ["get_product_stock", "invented_action"],
      "clarifyKey": null,
      "reason": "stock_with_code"
    }
    """
    result = ChatTurnAnalysisService.parse(
        raw,
        allowed_action_ids={"get_product_stock"},
        allowed_skill_keys={"sql", "company-knowledge"},
    )

    assert result is not None
    assert result.decision == "execute"
    assert result.action_ids == ("get_product_stock",)
    assert result.skills_to_load == ("sql",)


def test_parse_clarify_builds_direct_answer():
    raw = '{"decision":"clarify","clarifyKey":"ambiguous_domain","reason":"vague_term"}'
    result = ChatTurnAnalysisService.parse(raw)
    assert result is not None
    assert result.decision == "clarify"
    answer = result.direct_answer()
    assert answer
    assert "claro" in answer.lower() or "frase" in answer.lower()


def test_parse_execute_without_plan_becomes_clarify():
    raw = '{"decision":"execute","actionIds":[],"skillsToLoad":[],"reason":"empty"}'
    result = ChatTurnAnalysisService.parse(raw, allowed_action_ids={"a"})
    assert result is not None
    assert result.decision == "clarify"
    assert result.reason == "execute_without_plan"


def test_parse_rejects_invalid_decision():
    assert ChatTurnAnalysisService.parse('{"decision":"hack"}') is None


def test_safe_clarify_fallback():
    result = ChatTurnAnalysisService.safe_clarify(reason="boom")
    assert result.decision == "clarify"
    assert result.source == "fallback"
    assert result.direct_answer()
