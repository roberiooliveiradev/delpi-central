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


def test_gate_skips_fast_mode_and_unclear_stage():
    assert not ChatTurnAnalysisService.should_analyze(
        response_mode="fast",
        heuristic_intent="llm_general",
        heuristic_decision="llm_fallback",
        heuristic_reason="no_clear_intent",
    )
    assert not ChatTurnAnalysisService.should_analyze(
        response_mode="normal",
        heuristic_intent="llm_general",
        heuristic_decision="llm_fallback",
        heuristic_reason="no_clear_intent",
        pipeline_stages=["unclear_request"],
    )


def test_gate_skips_self_help_and_tools_already_skipped():
    assert not ChatTurnAnalysisService.should_analyze(
        response_mode="normal",
        heuristic_intent="self_help",
        heuristic_decision="direct",
        heuristic_reason="capabilities_catalog",
    )
    assert not ChatTurnAnalysisService.should_analyze(
        response_mode="normal",
        heuristic_intent="llm_general",
        heuristic_decision="llm_fallback",
        heuristic_reason="no_clear_intent",
        tools_already_skipped=True,
    )
    assert not ChatTurnAnalysisService.should_analyze(
        response_mode="normal",
        heuristic_intent="small_talk",
        heuristic_decision="small_talk",
        heuristic_reason="greeting_or_thanks",
    )


def test_gate_opens_on_no_clear_intent_normal():
    assert ChatTurnAnalysisService.should_analyze(
        response_mode="normal",
        heuristic_intent="llm_general",
        heuristic_decision="llm_fallback",
        heuristic_reason="no_clear_intent",
        heuristic_confidence=0.5,
    )


def test_parse_clarify_becomes_narrate_when_grounded():
    raw = '{"decision":"clarify","clarifyKey":"default","reason":"vague"}'
    result = ChatTurnAnalysisService.parse(raw, grounding_status="grounded")

    assert result is not None
    assert result.decision == "narrate"
    assert result.direct_answer() is None


def test_safe_clarify_becomes_narrate_when_grounded():
    result = ChatTurnAnalysisService.safe_clarify(
        reason="boom",
        grounding_status="grounded",
    )

    assert result.decision == "narrate"
    assert result.direct_answer() is None


def test_user_prompt_includes_grounding_block():
    prompt = ChatTurnAnalysisContentService.user_prompt(
        message="o que me diz sobre os itens?",
        response_mode="normal",
        heuristic_intent="operational_query",
        heuristic_confidence=0.4,
        heuristic_reason="no_clear_intent",
        skills_catalog="",
        actions_catalog="",
        grounding_status="grounded",
        last_result_excerpt={
            "title": "Estrutura 90260149",
            "rowCount": 6,
            "topKeys": ["10380044"],
        },
    )

    assert "grounded" in prompt
    assert "90260149" in prompt
    assert "10380044" in prompt
