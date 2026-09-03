from app.domain.services.chat_response_mode_service import ChatResponseModeService
from app.domain.services.chat_turn_mode_service import ChatTurnModeService


def test_turn_mode_consume_prior_for_drawing_direct_answer():
    mode = ChatTurnModeService.resolve(
        message="confirmar revisão manual",
        tool_context={"drawingAnalysisMode": True, "directAnswer": "ok"},
        direct_answer="ok",
        pipeline_stages=["drawing_analysis"],
    )

    assert mode == ChatTurnModeService.CONSUME_PRIOR
    assert ChatTurnModeService.should_skip_llm(mode)
    assert ChatTurnModeService.should_skip_agentic(mode)


def test_turn_mode_ask_slot_for_missing_required_parameter():
    mode = ChatTurnModeService.resolve(
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": False,
                    "errorKind": "missing_required_parameter",
                    "missingParameter": "code",
                },
            }
        ],
    )

    assert mode == ChatTurnModeService.ASK_SLOT


def test_response_mode_honors_turn_mode_consume_prior():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="confirmar revisão",
        response_mode="normal",
        direct_answer="Relatório revisado.",
        skip_rag=True,
        tool_calls=[],
        tool_context={"drawingAnalysisMode": True},
        pipeline_stages=["drawing_analysis"],
    )

    assert direct == "Relatório revisado."
    assert effect == "simple_direct"
    assert skip_rag is True


def test_turn_mode_analyze_before_tools():
    mode = ChatTurnModeService.resolve(
        message="programação e qualidade",
        tool_context={
            "turnAnalysis": {"decision": "execute"},
            "turnAnalysisActionIds": ["schedule", "quality"],
        },
        tool_calls=[],
    )

    assert mode == ChatTurnModeService.ANALYZE
    assert ChatTurnModeService.should_skip_llm(mode)
    assert ChatTurnModeService.should_skip_agentic(mode)


def test_turn_mode_compose_after_tools():
    mode = ChatTurnModeService.resolve(
        message="estoque e fornecedores 10080022",
        tool_context={
            "turnAnalysis": {"decision": "execute"},
            "turnAnalysisSkillsToLoad": ["company-knowledge"],
            "turnAnalysisActionIds": ["stock", "suppliers"],
        },
        tool_calls=[{"name": "execute_external_action", "metadata": {"ok": True}}],
    )

    assert mode == ChatTurnModeService.COMPOSE
    assert not ChatTurnModeService.should_skip_llm(mode)


def test_turn_mode_consume_prior_for_unclear_request():
    mode = ChatTurnModeService.resolve(
        message="programação",
        direct_answer="Não ficou claro o que você quer com esse termo.",
        pipeline_stages=["unclear_request"],
        tool_calls=[],
    )

    assert mode == ChatTurnModeService.CONSUME_PRIOR
    assert ChatTurnModeService.should_skip_llm(mode)
    assert ChatTurnModeService.should_skip_agentic(mode)


def test_turn_mode_llm_narrate_for_data_interpretation_insight():
    mode = ChatTurnModeService.resolve(
        message="interprete o resultado da última consulta SQL",
        tool_context={"requiresDataInterpretationLlm": True, "directAnswer": "template fraco"},
        direct_answer="template fraco",
        pipeline_stages=["grounded_narrate_insight"],
        tool_calls=[],
    )

    assert mode == ChatTurnModeService.LLM_NARRATE
    assert not ChatTurnModeService.should_skip_llm(mode)


def test_response_mode_clears_direct_answer_for_insight_llm():
    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="interprete o resultado da última consulta SQL",
        response_mode="normal",
        direct_answer="Foram retornados 2 registros.",
        skip_rag=True,
        tool_calls=[],
        tool_context={"requiresDataInterpretationLlm": True},
        pipeline_stages=["grounded_narrate_insight", "data_interpretation_llm"],
    )

    assert direct is None
    assert effect == "llm_synthesis"
    assert skip_rag is True
